"""
SDD Evolution Engine — Skill-Driven Development optimizer.

Replaces the legacy DSPy/GEPA + Ollama pipeline with a direct cloud-LLM
approach that follows the SDD spec:

  1. Extract variables from skill templates
  2. Iterative refinement (semantic → format → token+edge-cases)
  3. Structured JSON output with system prompt, template, constraints
  4. Save metrics compatible with the dashboard

Usage:
    python sdd_evolve.py --skill github-code-review --iterations 3
"""

import argparse
import json
import os
import re
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# ── Configuration ──────────────────────────────────────────────────

# Provider selection: explicit env vars > cloud keys > Ollama fallback
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
NOUS_KEY = os.getenv("NOUS_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_BASE = os.getenv("OLLAMA_API_BASE", "")
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "")

# Normalize Ollama URLs so they always end with /v1
def _norm_ollama(url: str) -> str:
    if url and not url.rstrip("/").endswith("/v1"):
        return url.rstrip("/") + "/v1"
    return url

# If main.py explicitly set OPENAI_BASE_URL to an Ollama endpoint, respect it.
_is_ollama_url = "11434" in OPENAI_BASE or "ollama" in OPENAI_BASE.lower() or "11434" in OLLAMA_BASE

if _is_ollama_url:
    # Prefer OPENAI_BASE_URL when it points to Ollama (set by main.py)
    API_BASE = _norm_ollama(OPENAI_BASE) if OPENAI_BASE else _norm_ollama(OLLAMA_BASE) or "http://localhost:11434/v1"
    API_KEY = OPENAI_KEY or "ollama"
    DEFAULT_MODEL = os.getenv("SDD_EVOLVE_MODEL", os.getenv("SDD_OLLAMA_MODEL", "gemma4:31b-cloud"))
    print(f"[INFO] Using Ollama local at {API_BASE} with model {DEFAULT_MODEL}", flush=True)
elif OPENROUTER_KEY:
    API_BASE = OPENAI_BASE or "https://openrouter.ai/api/v1"
    API_KEY = OPENROUTER_KEY
    DEFAULT_MODEL = os.getenv("SDD_EVOLVE_MODEL", "anthropic/claude-sonnet-4")
    print(f"[INFO] Using OpenRouter with model {DEFAULT_MODEL}", flush=True)
elif NOUS_KEY:
    API_BASE = OPENAI_BASE or "https://inference-api.nousresearch.com/v1"
    API_KEY = NOUS_KEY
    DEFAULT_MODEL = os.getenv("SDD_EVOLVE_MODEL", "moonshotai/kimi-k2.6")
    print(f"[INFO] Using Nous API with model {DEFAULT_MODEL}", flush=True)
elif ANTHROPIC_KEY:
    API_BASE = OPENAI_BASE or "https://api.anthropic.com/v1"
    API_KEY = ANTHROPIC_KEY
    DEFAULT_MODEL = os.getenv("SDD_EVOLVE_MODEL", "claude-sonnet-4-20250514")
    print(f"[INFO] Using Anthropic API with model {DEFAULT_MODEL}", flush=True)
else:
    # Ultimate fallback: Ollama local
    API_BASE = "http://localhost:11434/v1"
    API_KEY = "ollama"
    DEFAULT_MODEL = os.getenv("SDD_EVOLVE_MODEL", "gemma4:31b-cloud")
    print(f"[INFO] No cloud keys found — falling back to Ollama local at {API_BASE} with model {DEFAULT_MODEL}", flush=True)

SKILL_SEARCH_PATHS = [
    Path.home() / ".hermes" / "global_skills",
    Path.home() / ".hermes" / "skills",
    Path.home() / ".claude" / "skills",
    Path.home() / ".opencode" / "skills",
]

# ── Logging helpers (dashboard job-tracker parses these) ───────────

class Logger:
    def __init__(self):
        self._phases = []

    def phase(self, msg: str):
        print(f"[PHASE] {msg}", flush=True)

    def info(self, msg: str):
        print(f"[INFO] {msg}", flush=True)

    def ok(self, msg: str):
        print(f"[OK] {msg}", flush=True)

    def warn(self, msg: str):
        print(f"[WARN] {msg}", flush=True)

    def err(self, msg: str):
        print(f"[ERROR] {msg}", flush=True)

    def metric(self, key: str, value):
        print(f"[METRIC] {key}={value}", flush=True)

    def score(self, label: str, value: float):
        print(f"[SCORE] {label}={value:.4f}", flush=True)

log = Logger()

# ── LLM client ─────────────────────────────────────────────────────

def _get_client():
    try:
        from openai import OpenAI
    except ImportError:
        log.err("openai package not installed. Run: pip install openai")
        sys.exit(1)

    if not API_KEY:
        log.err("No API key found. Set OPENROUTER_API_KEY or NOUS_API_KEY in ~/.hermes/.env")
        sys.exit(1)

    return OpenAI(base_url=API_BASE, api_key=API_KEY)


def chat_completion(messages: list, model: str = DEFAULT_MODEL, temperature: float = 0.4, max_tokens: int = 4000) -> str:
    client = _get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


# ── Skill loader ───────────────────────────────────────────────────

def find_skill(name: str) -> Optional[Path]:
    for base in SKILL_SEARCH_PATHS:
        if not base.exists():
            continue
        # Direct match: base/name/SKILL.md or base/name.md
        direct = base / name / "SKILL.md"
        if direct.exists():
            return direct
        direct2 = base / f"{name}.md"
        if direct2.exists():
            return direct2
        # Search one level deep
        for child in base.iterdir():
            if child.name.lower() == name.lower():
                if child.is_dir():
                    for cand in ["SKILL.md", "skill.md", "README.md", "index.md"]:
                        p = child / cand
                        if p.exists():
                            return p
                elif child.suffix == ".md":
                    return child
    return None


def load_skill(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    # Parse frontmatter
    frontmatter = {}
    body = raw
    if raw.strip().startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            try:
                import yaml
                frontmatter = yaml.safe_load(parts[1]) or {}
            except Exception:
                frontmatter = {}
            body = parts[2]

    # Extract variables {{var}}
    variables = sorted(set(re.findall(r"\{\{\s*(\w+)\s*\}\}", raw)))

    return {
        "path": path,
        "name": path.parent.name if path.name == "SKILL.md" else path.stem,
        "raw": raw,
        "frontmatter": frontmatter,
        "body": body,
        "variables": variables,
        "size": len(raw),
    }


# ── Prompt builders ────────────────────────────────────────────────

def build_iter1_prompt(skill: dict) -> str:
    vars_block = "\n".join(f"  - {{{{{v}}}}}" for v in skill["variables"]) or "  (none detected)"
    return textwrap.dedent(f"""\
    You are an expert Prompt Engineer specializing in Skill-Driven Development (SDD).

    TASK: Improve the semantic clarity and logical flow of the following skill.

    RULES:
    - Preserve ALL template variables exactly as {{{{varName}}}} — do not rename or remove them.
    - Keep the same overall purpose and domain.
    - Fix ambiguous instructions, tighten wording, and ensure a clear step-by-step flow.
    - Add a concise "System_Prompt" section at the top if missing.
    - Do NOT change the output format yet (that comes next iteration).

    DETECTED VARIABLES:
    {vars_block}

    ORIGINAL SKILL:
    {skill['raw'][:4000]}

    OUTPUT: Return ONLY the improved skill markdown (with frontmatter). No explanations outside the markdown.
    """)


def build_iter2_prompt(skill: dict, iter1_text: str) -> str:
    vars_block = "\n".join(f"  - {{{{{v}}}}}" for v in skill["variables"]) or "  (none detected)"
    return textwrap.dedent(f"""\
    You are an expert Prompt Engineer specializing in Skill-Driven Development (SDD).

    TASK: Structure the output format of the following skill. Ensure it produces valid, parseable responses.

    RULES:
    - Preserve ALL template variables exactly as {{{{varName}}}}.
    - Define a clear response format: prefer structured JSON or well-defined Markdown sections.
    - Add Few-Shot examples (input → expected output) when helpful.
    - Include a "Formato de Respuesta" section describing the exact output schema.
    - If JSON output is appropriate, specify the JSON schema inline.

    DETECTED VARIABLES:
    {vars_block}

    SKILL AFTER ITERATION 1 (semantic clarity):
    {iter1_text[:4000]}

    OUTPUT: Return ONLY the improved skill markdown. No explanations outside the markdown.
    """)


def build_iter3_prompt(skill: dict, iter2_text: str) -> str:
    vars_block = "\n".join(f"  - {{{{{v}}}}}" for v in skill["variables"]) or "  (none detected)"
    return textwrap.dedent(f"""\
    You are an expert Prompt Engineer specializing in Skill-Driven Development (SDD).

    TASK: Optimize token consumption and add edge-case handling.

    RULES:
    - Preserve ALL template variables exactly as {{{{varName}}}}.
    - Remove redundant prose. Make every sentence earn its tokens.
    - Add explicit Constraints section with strict rules (e.g., "No respondas con prosa, solo código").
    - Add Error Handling instructions for invalid/ambiguous inputs.
    - Include Validation Rules as a checklist.
    - Add a brief Meta-Data section describing the skill's capabilities and limits.

    DETECTED VARIABLES:
    {vars_block}

    SKILL AFTER ITERATION 2 (structured format):
    {iter2_text[:4000]}

    OUTPUT: Return ONLY the final evolved skill markdown. No explanations outside the markdown.
    """)


def build_sdd_json_prompt(skill_name: str, final_md: str, iterations: int) -> str:
    return textwrap.dedent(f"""\
    You are an SDD (Skill-Driven Development) architect.

    TASK: Analyze the evolved skill below and produce a structured SDD analysis JSON.

    RULES:
    - The "refined_prompt.system" should be the core identity instructions extracted from the skill.
    - The "refined_prompt.template" should be the reusable user-facing template with variable placeholders.
    - "validation_rules" must be a list of specific, testable constraints.
    - "sdd_analysis" should explain why this version is more robust for system integration.

    EVOLVED SKILL:
    {final_md[:4000]}

    OUTPUT ONLY valid JSON matching this exact schema (no markdown fences):
    {{
      "skill_name": "{skill_name}",
      "iteration": {iterations},
      "refined_prompt": {{
        "system": "...",
        "template": "...",
        "validation_rules": ["..."]
      }},
      "sdd_analysis": "..."
    }}
    """)


# ── Quality scoring ────────────────────────────────────────────────

def score_skill(text: str, original: str) -> dict:
    """Compute heuristic quality metrics."""
    scores = {}

    # Structure score: has frontmatter, sections, constraints
    has_fm = text.strip().startswith("---")
    has_constraints = "constraint" in text.lower() or "restricción" in text.lower()
    has_examples = "ejemplo" in text.lower() or "example" in text.lower() or "```" in text
    has_json_schema = "json" in text.lower() and ("schema" in text.lower() or "formato" in text.lower())
    scores["structure"] = min(1.0, (0.25 * has_fm + 0.25 * has_constraints + 0.25 * has_examples + 0.25 * has_json_schema))

    # Length efficiency: not too much longer, not too much shorter
    orig_len = len(original)
    new_len = len(text)
    ratio = new_len / max(orig_len, 1)
    scores["efficiency"] = 1.0 - abs(ratio - 1.0)  # peak at 1.0x, drops if diverges
    scores["efficiency"] = max(0.0, min(1.0, scores["efficiency"]))

    # Variable preservation
    orig_vars = set(re.findall(r"\{\{\s*(\w+)\s*\}\}", original))
    new_vars = set(re.findall(r"\{\{\s*(\w+)\s*\}\}", text))
    if orig_vars:
        scores["variable_preservation"] = len(new_vars & orig_vars) / len(orig_vars)
    else:
        scores["variable_preservation"] = 1.0

    # Composite evolved score
    scores["evolved_score"] = round(
        0.4 * scores["structure"] + 0.3 * scores["efficiency"] + 0.3 * scores["variable_preservation"],
        4,
    )
    scores["baseline_score"] = 0.5  # heuristic baseline
    scores["improvement"] = round(scores["evolved_score"] - scores["baseline_score"], 4)
    return scores


# ── Main evolution loop ────────────────────────────────────────────

def evolve_skill(skill_name: str, iterations: int = 3, hermes_repo: Optional[str] = None):
    start_time = time.time()
    log.phase(f"Starting SDD evolution for skill: {skill_name}")
    log.info(f"Iterations: {iterations}, Model: {DEFAULT_MODEL}")

    # 1. Load skill
    skill_path = find_skill(skill_name)
    if not skill_path:
        log.err(f"Skill '{skill_name}' not found in any search path")
        sys.exit(1)

    skill = load_skill(skill_path)
    log.ok(f"Loaded skill from {skill_path}")
    log.info(f"Size: {skill['size']} chars | Variables: {skill['variables']}")
    log.metric("baseline_size", skill["size"])

    # 2. Run iterative refinement
    current_text = skill["raw"]

    for i in range(1, iterations + 1):
        log.phase(f"Iteration {i}/{iterations}")
        if i == 1:
            prompt = build_iter1_prompt(skill)
            label = "semantic clarity"
        elif i == 2:
            prompt = build_iter2_prompt(skill, current_text)
            label = "format structure"
        else:
            prompt = build_iter3_prompt(skill, current_text)
            label = "token optimization + edge cases"

        log.info(f"Optimizing for: {label}")
        try:
            messages = [{"role": "system", "content": "You are a world-class prompt engineer."}, {"role": "user", "content": prompt}]
            current_text = chat_completion(messages, temperature=0.3 if i < 3 else 0.2)
            log.ok(f"Iteration {i} complete ({len(current_text)} chars)")
        except Exception as e:
            log.err(f"LLM call failed at iteration {i}: {e}")
            sys.exit(1)

    # 3. Generate SDD JSON analysis
    log.phase("Generating SDD analysis")
    try:
        sdd_json_text = chat_completion(
            [{"role": "system", "content": "You output only valid JSON."},
             {"role": "user", "content": build_sdd_json_prompt(skill_name, current_text, iterations)}],
            temperature=0.1,
            max_tokens=3000,
        )
        # Clean up potential markdown fences
        sdd_json_text = re.sub(r"^```json\s*|\s*```$", "", sdd_json_text.strip(), flags=re.MULTILINE)
        sdd_data = json.loads(sdd_json_text)
        log.ok("SDD analysis generated")
    except Exception as e:
        log.warn(f"Could not generate structured SDD analysis: {e}")
        sdd_data = {
            "skill_name": skill_name,
            "iteration": iterations,
            "refined_prompt": {"system": "", "template": "", "validation_rules": []},
            "sdd_analysis": "SDD analysis generation failed.",
        }

    # 4. Score
    log.phase("Evaluating evolved skill")
    scores = score_skill(current_text, skill["raw"])
    for k, v in scores.items():
        log.score(k, v)

    # 5. Save outputs
    output_base = Path.home() / ".hermes" / "hermes-agent-self-evolution" / "output" / skill_name
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_base / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    evolved_path = run_dir / "evolved_skill.md"
    evolved_path.write_text(current_text, encoding="utf-8")

    baseline_path = run_dir / "baseline_skill.md"
    baseline_path.write_text(skill["raw"], encoding="utf-8")

    sdd_path = run_dir / "sdd_analysis.json"
    sdd_path.write_text(json.dumps(sdd_data, indent=2, ensure_ascii=False), encoding="utf-8")

    metrics = {
        "skill_name": skill_name,
        "timestamp": datetime.now().isoformat(),
        "baseline_score": scores["baseline_score"],
        "evolved_score": scores["evolved_score"],
        "improvement": scores["improvement"],
        "elapsed_seconds": round(time.time() - start_time, 2),
        "iterations": iterations,
        "optimizer_model": DEFAULT_MODEL,
        "eval_model": DEFAULT_MODEL,
        "constraints_passed": scores["structure"] > 0.6,
        "original_size": skill["size"],
        "evolved_size": len(current_text),
        "diff_lines": len(current_text.splitlines()) - len(skill["raw"].splitlines()),
        "sdd_analysis": sdd_data,
    }
    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    log.ok(f"Saved outputs to {run_dir}")
    log.score("final_evolved_score", scores["evolved_score"])
    log.phase("Evolution complete")

    return metrics


# ── CLI entrypoint ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SDD Skill Evolution Engine")
    parser.add_argument("--skill", required=True, help="Skill name to evolve")
    parser.add_argument("--iterations", type=int, default=3, help="Number of evolution iterations")
    parser.add_argument("--hermes-repo", default=None, help="Path to hermes repo (unused, kept for compat)")
    parser.add_argument("--eval-source", default="synthetic", help="Dataset source (unused, kept for compat)")
    args = parser.parse_args()

    evolve_skill(args.skill, args.iterations, args.hermes_repo)


if __name__ == "__main__":
    main()
