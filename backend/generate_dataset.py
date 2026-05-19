"""
Dataset Generator — Genera ejemplos de validación sintéticos para skills.

Usage:
    python generate_dataset.py --skill code-review --count 10 --output ~/.hermes/datasets/code-review/train.jsonl
"""
import argparse
import json
import sys
from pathlib import Path
from openai import OpenAI

OLLAMA_BASE = "http://localhost:11434/v1"
OLLAMA_MODEL = "gemma4:31b-cloud"

client = OpenAI(base_url=OLLAMA_BASE, api_key="ollama")

SKILL_PROMPTS = {
    "code-review": """Para la skill 'code-review', generá exactamente {count} ejemplos de revisión de código.
Cada ejemplo debe ser un objeto JSON con:
- "input": código con bugs/problemas (Python, TypeScript, o Go)
- "expected": la revisión esperada (bugs específicos que deberían detectarse)

Cubrí estos casos:
1. Python: SQL injection, type hints faltantes, async mal usado, raw dicts en vez de Pydantic
2. TypeScript/React: useEffect sin deps, componentes no memoizados, keys faltantes en maps
3. Go: error handling ignorado, goroutines sin sync, nil pointer dereference
4. General: dead code, secretos hardcodeados, logs con PII

IMPORTANTE: El expected NO debe ser el código corregido, sino una LISTA de bugs que deben detectarse.

OUTPUT: Array JSON de objetos {{"input": "...", "expected": "..."}}. Sin markdown fences.
Generá EXACTAMENTE {count} ejemplos. Comenzá YA:""",
}


def generate_dataset(skill: str, count: int, output_path: str):
    prompt = SKILL_PROMPTS.get(skill, SKILL_PROMPTS["code-review"]).format(count=count)
    
    print(f"🎯 Generating {count} examples for '{skill}'...", flush=True)
    
    resp = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": "Sos un experto en code review. Generás datasets de validación en JSON. Output: solo JSON válido, sin explicaciones."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000,
    )
    
    raw = resp.choices[0].message.content or ""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    
    try:
        examples = json.loads(raw)
    except json.JSONDecodeError:
        print(f"❌ Failed to parse JSON. Raw output:", file=sys.stderr)
        print(raw[:500], file=sys.stderr)
        sys.exit(1)
    
    if not isinstance(examples, list):
        examples = [examples]
    
    # Write to file
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    
    print(f"✅ Saved {len(examples)} examples to {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic validation dataset")
    parser.add_argument("--skill", required=True, help="Skill name")
    parser.add_argument("--count", type=int, default=10, help="Number of examples")
    parser.add_argument("--output", required=True, help="Output .jsonl file")
    args = parser.parse_args()
    generate_dataset(args.skill, args.count, args.output)
