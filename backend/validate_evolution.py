"""
Evolution Validator — LLM Judge que compara skill original vs evolucionada.

Flujo:
  1. Carga skill original y evolucionada
  2. Corre ambas contra el dataset de validación (holdout.jsonl)
  3. LLM Judge evalúa cada output en 4 dimensiones
  4. Veredicto final: PASS / MIXED / FAIL

Usage:
    python validate_evolution.py --skill code-review --run 20260428_015945
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────
OLLAMA_BASE = "http://localhost:11434/v1"
OLLAMA_MODEL = "gemma4:31b-cloud"
EVOLUTION_DIR = Path.home() / ".hermes" / "hermes-agent-self-evolution" / "output"
DATASETS_DIR = Path.home() / ".hermes" / "datasets"

client = OpenAI(base_url=OLLAMA_BASE, api_key="ollama")


# ── Skill runner (simple) ──────────────────────────────────────────
def run_skill(skill_content: str, code_input: str) -> str:
    """Ejecuta la skill contra un input — simula lo que haría Hermes."""
    resp = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": skill_content[:3000]},
            {"role": "user", "content": code_input}
        ],
        temperature=0.2,
        max_tokens=1500,
    )
    return resp.choices[0].message.content or ""


# ── LLM Judge ──────────────────────────────────────────────────────
JUDGE_PROMPT = """Sos un juez experto en calidad de code reviews.
Compará DOS revisiones de código del mismo input.

INPUT ORIGINAL:
{code_input}

REVIEW A (skill original):
{output_a}

REVIEW B (skill evolucionada):
{output_b}

Evaluá CADA UNA en estas 4 dimensiones (puntaje 1-10):

1. Corrección (35%): ¿Detecta todos los bugs reales? ¿No alucina problemas inexistentes?
2. Precisión (25%): ¿Señala ubicaciones exactas? ¿Sugerencias son accionables? ¿Código de ejemplo?
3. Cobertura (25%): ¿Cubre seguridad, tipos, async, edge cases, performance, estilo?
4. Concisión (15%): ¿Va al punto? ¿Sin relleno innecesario?

Luego respondé en este formato EXACTO (sin markdown, sin explicaciones adicionales):

VEREDICT: <PASS|MIXED|FAIL>
A_CORRECCION: <1-10>
A_PRECISION: <1-10>
A_COBERTURA: <1-10>
A_CONCISION: <1-10>
B_CORRECCION: <1-10>
B_PRECISION: <1-10>
B_COBERTURA: <1-10>
B_CONCISION: <1-10>
REASON: <una frase explicando el veredicto>"""


def judge_output(code_input: str, output_a: str, output_b: str) -> Optional[dict]:
    """LLM Judge evalúa A vs B."""
    prompt = JUDGE_PROMPT.format(
        code_input=code_input[:2000],
        output_a=output_a[:2000],
        output_b=output_b[:2000],
    )
    
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800,
            )
            raw = resp.choices[0].message.content or ""
            
            # Parsear
            verdict = re.search(r"VEREDICT:\s*(PASS|MIXED|FAIL)", raw)
            if not verdict:
                continue
            
            scores = {}
            for dim in ["A_CORRECCION", "A_PRECISION", "A_COBERTURA", "A_CONCISION",
                       "B_CORRECCION", "B_PRECISION", "B_COBERTURA", "B_CONCISION"]:
                m = re.search(rf"{dim}:\s*(\d+)", raw)
                scores[dim.lower()] = int(m.group(1)) if m else 5
            
            reason = re.search(r"REASON:\s*(.+?)$", raw, re.MULTILINE)
            
            return {
                "verdict": verdict.group(1),
                "scores_a": {
                    "correccion": scores["a_correccion"],
                    "precision": scores["a_precision"],
                    "cobertura": scores["a_cobertura"],
                    "concision": scores["a_concision"],
                },
                "scores_b": {
                    "correccion": scores["b_correccion"],
                    "precision": scores["b_precision"],
                    "cobertura": scores["b_cobertura"],
                    "concision": scores["b_concision"],
                },
                "reason": reason.group(1).strip() if reason else "N/A",
                "raw_judge": raw,
            }
        except Exception as e:
            print(f"  ⚠️ Judge attempt {attempt+1} failed: {e}")
            time.sleep(2)
    
    return None


# ── Main ────────────────────────────────────────────────────────────
def validate_evolution(skill_name: str, run_dir: Optional[str] = None):
    print(f"🧬 Validating evolution: {skill_name}")
    
    # 1. Find latest run
    skill_output = EVOLUTION_DIR / skill_name
    if not skill_output.exists():
        print(f"❌ No evolution output for '{skill_name}'")
        return None
    
    if run_dir:
        run_path = skill_output / run_dir
    else:
        runs = sorted([d for d in skill_output.iterdir() if d.is_dir()], key=lambda d: d.stat().st_mtime)
        if not runs:
            print(f"❌ No evolution runs for '{skill_name}'")
            return None
        run_path = runs[-1]
        run_dir = run_path.name
    
    print(f"   Run: {run_dir}")
    
    # 2. Load skills
    baseline_path = run_path / "baseline_skill.md"
    evolved_path = run_path / "evolved_skill.md"
    
    if not baseline_path.exists() or not evolved_path.exists():
        print(f"❌ Missing baseline or evolved skill files")
        return None
    
    baseline = baseline_path.read_text()
    evolved = evolved_path.read_text()
    print(f"   Baseline: {len(baseline)} chars → Evolved: {len(evolved)} chars")
    
    # 3. Load holdout dataset
    holdout_path = DATASETS_DIR / skill_name / "holdout.jsonl"
    if not holdout_path.exists():
        print(f"⚠️  No holdout.jsonl for '{skill_name}'. Using built-in tests.")
        test_cases = [
            {"input": "Revisá:\n```python\ndef get_user(id):\n    return db.execute(f\"SELECT * FROM users WHERE id = {id}\")\n```", 
             "expected": "SQL injection + sin type hints + sin manejo errores"},
        ]
    else:
        test_cases = []
        with open(holdout_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    test_cases.append(json.loads(line))
        print(f"   Holdout: {len(test_cases)} test cases")
    
    # 4. Run both skills against holdout
    results = []
    for i, tc in enumerate(test_cases):
        print(f"\n   ── Test {i+1}/{len(test_cases)} ──")
        
        # Run skill A (original)
        print(f"   Running skill A (original)...", end=" ", flush=True)
        t0 = time.time()
        out_a = run_skill(baseline, tc["input"])
        print(f"{len(out_a)} chars, {time.time()-t0:.1f}s")
        
        # Run skill B (evolved)
        print(f"   Running skill B (evolved)...", end=" ", flush=True)
        t0 = time.time()
        out_b = run_skill(evolved, tc["input"])
        print(f"{len(out_b)} chars, {time.time()-t0:.1f}s")
        
        # Judge
        print(f"   🧑‍⚖️ LLM Judge evaluating...", end=" ", flush=True)
        judgment = judge_output(tc["input"], out_a, out_b)
        if judgment:
            print(f"→ {judgment['verdict']}")
            results.append({
                "test_id": i + 1,
                "verdict": judgment["verdict"],
                "scores_a": judgment["scores_a"],
                "scores_b": judgment["scores_b"],
                "reason": judgment["reason"],
            })
        else:
            print(f"→ ❌ Judge failed")
            results.append({"test_id": i + 1, "verdict": "ERROR", "reason": "Judge failed"})
    
    # 5. Compute final verdict
    passes = sum(1 for r in results if r["verdict"] == "PASS")
    mixed = sum(1 for r in results if r["verdict"] == "MIXED")
    fails = sum(1 for r in results if r["verdict"] == "FAIL")
    
    if passes >= len(results) * 0.8 and fails == 0:
        final = "PASS ✅"
    elif fails > 0:
        final = "FAIL ❌"
    else:
        final = "MIXED ⚠️"
    
    # 6. Report
    report = {
        "skill_name": skill_name,
        "run_dir": run_dir,
        "timestamp": datetime.now().isoformat(),
        "final_verdict": final,
        "summary": {
            "pass": passes,
            "mixed": mixed,
            "fail": fails,
            "total": len(results),
        },
        "details": results,
        "baseline_size": len(baseline),
        "evolved_size": len(evolved),
    }
    
    print(f"\n{'='*60}")
    print(f"  FINAL VERDICT: {final}")
    print(f"  PASS={passes} MIXED={mixed} FAIL={fails} (total={len(results)})")
    print(f"{'='*60}")
    
    # Save report
    report_path = run_path / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n📄 Report saved to {report_path}")
    
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate skill evolution with LLM Judge")
    parser.add_argument("--skill", required=True, help="Skill name")
    parser.add_argument("--run", default=None, help="Run directory (default: latest)")
    args = parser.parse_args()
    validate_evolution(args.skill, args.run)
