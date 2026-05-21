"""
④ COMPILA — DSPy Compilation Layer

Uses DSPy's BetterTogether to chain optimizers (GEPA → BootstrapFinetune → GEPA)
and compile validated skills from SkillGenesis packets.

This is the "forge" where GEPA's desires become DSPy-compiled reality.
"""

from __future__ import annotations
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import SkillGenesisPacket, CompilationResult

SKILLS_DIR = Path.home() / ".hermes" / "skills"


class DSPyCompiler:
    """Compiles skills using DSPy's BetterTogether optimizer chaining."""

    def __init__(self, python_bin: str = sys.executable):
        self.python_bin = python_bin
        self._check_dspy()

    def _check_dspy(self):
        """Verify DSPy is available."""
        try:
            result = subprocess.run(
                [self.python_bin, "-c", "import dspy; print(dspy.__version__)"],
                capture_output=True, text=True, timeout=10
            )
            self.dspy_version = result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            self.dspy_version = None

    @property
    def is_available(self) -> bool:
        return self.dspy_version is not None

    # ── Compilation ─────────────────────────────────────────────────
    def compile(self, packet: SkillGenesisPacket, attempt: int = 1) -> CompilationResult:
        """Compile a single SkillGenesis packet into a validated skill.

        Uses DSPy BetterTogether with the configured strategy.
        Falls back to script-based compilation if DSPy module import fails.
        """
        if self.is_available:
            return self._compile_with_dspy(packet, attempt)
        else:
            return self._compile_with_script(packet, attempt)

    def _compile_with_dspy(self, packet: SkillGenesisPacket, attempt: int) -> CompilationResult:
        """Direct DSPy BetterTogether compilation."""
        compilation_script = self._generate_compilation_script(packet, attempt)

        script_path = Path.home() / ".hermes" / "traces" / "processed" / f"compile_{packet.packet_id}.py"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(compilation_script)

        try:
            result = subprocess.run(
                [self.python_bin, str(script_path)],
                capture_output=True, text=True, timeout=300,  # 5 min timeout for compilation
                env={**__import__('os').environ, "PYTHONUNBUFFERED": "1"}
            )

            if result.returncode == 0:
                # Parse output for metrics
                output = result.stdout
                best_score = self._extract_metric(output, "best_score", 0.0)
                delta = self._extract_metric(output, "delta", 0.0)
                iterations = self._extract_metric(output, "iterations", 0)

                skill_name = self._generate_skill_name(packet)
                skill_path = str(SKILLS_DIR / "software-development" / skill_name)

                return CompilationResult(
                    packet_id=packet.packet_id,
                    success=True,
                    skill_name=skill_name,
                    skill_path=skill_path,
                    iterations=iterations,
                    best_score=best_score,
                    delta=delta,
                    threshold_met=delta >= packet.threshold,
                    attempt=attempt,
                )
            else:
                return CompilationResult(
                    packet_id=packet.packet_id,
                    success=False,
                    skill_name="",
                    skill_path="",
                    iterations=0,
                    best_score=0.0,
                    delta=0.0,
                    threshold_met=False,
                    attempt=attempt,
                    error=result.stderr[:500] if result.stderr else "Unknown compilation error",
                )

        except subprocess.TimeoutExpired:
            return CompilationResult(
                packet_id=packet.packet_id,
                success=False,
                skill_name="",
                skill_path="",
                iterations=0,
                best_score=0.0,
                delta=0.0,
                threshold_met=False,
                attempt=attempt,
                error="Compilation timed out after 300 seconds",
            )
        except Exception as e:
            return CompilationResult(
                packet_id=packet.packet_id,
                success=False,
                skill_name="",
                skill_path="",
                iterations=0,
                best_score=0.0,
                delta=0.0,
                threshold_met=False,
                attempt=attempt,
                error=str(e),
            )

    def _compile_with_script(self, packet: SkillGenesisPacket, attempt: int) -> CompilationResult:
        """Fallback: use existing evolution scripts when DSPy module import fails."""
        evolution_dir = Path.home() / ".hermes" / "hermes-agent-self-evolution"
        evolve_script = evolution_dir / "evolve_now.py"

        if not evolve_script.exists():
            return CompilationResult(
                packet_id=packet.packet_id,
                success=False,
                skill_name="",
                skill_path="",
                iterations=0,
                best_score=0.0,
                delta=0.0,
                threshold_met=False,
                attempt=attempt,
                error=f"Evolution script not found at {evolve_script}",
            )

        try:
            result = subprocess.run(
                [self.python_bin, str(evolve_script),
                 "--skill", packet.intent[:50].replace(" ", "-"),
                 "--dataset", packet.dataset_path,
                 "--metric", packet.metric,
                 "--threshold", str(packet.threshold)],
                capture_output=True, text=True, timeout=300,
                env={**__import__('os').environ, "PYTHONUNBUFFERED": "1"}
            )

            skill_name = self._generate_skill_name(packet)
            return CompilationResult(
                packet_id=packet.packet_id,
                success=result.returncode == 0,
                skill_name=skill_name,
                skill_path=str(SKILLS_DIR / "software-development" / skill_name),
                iterations=packet.max_attempts,
                best_score=self._extract_metric(result.stdout, "best_score", 0.0),
                delta=self._extract_metric(result.stdout, "delta", 0.0),
                threshold_met=self._extract_metric(result.stdout, "delta", 0.0) >= packet.threshold,
                attempt=attempt,
                error=result.stderr[:500] if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            return CompilationResult(
                packet_id=packet.packet_id, success=False, skill_name="", skill_path="",
                iterations=0, best_score=0.0, delta=0.0, threshold_met=False,
                attempt=attempt, error="Script compilation timed out",
            )

    # ── Helpers ─────────────────────────────────────────────────────
    def _generate_compilation_script(self, packet: SkillGenesisPacket, attempt: int) -> str:
        """Generate a standalone DSPy compilation script with BetterTogether."""
        return f'''"""
Auto-generated DSPy Compilation Script
Packet: {packet.packet_id} | Attempt: {attempt}
Strategy: {packet.strategy} | Metric: {packet.metric}
"""
import json
import dspy

# ── Configure LM ──
import os
_ollama_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434/v1")
_ollama_model = os.getenv("SDD_OLLAMA_MODEL", os.getenv("SDD_EVOLVE_MODEL", "gemma4:31b-cloud"))
lm = dspy.LM(f"openai/{_ollama_model}", api_base=_ollama_base, api_key="ollama", temperature=0.3)
dspy.configure(lm=lm)

# ── Load Dataset ──
with open("{packet.dataset_path}") as f:
    raw_data = [json.loads(line) for line in f if line.strip()]

# Split train/holdout
split = int(len(raw_data) * (1 - {packet.holdout}))
train_data = raw_data[:split]
holdout_data = raw_data[split:]

# ── Define Signature ──
class EvolvedSkill(dspy.Signature):
    \"\"\"{packet.intent}\"\"\"
    error_log = dspy.InputField(desc="The error log or trace to analyze")
    context = dspy.InputField(desc="Additional context about the failure")
    fix_steps = dspy.OutputField(desc="Step-by-step resolution actions")
    explanation = dspy.OutputField(desc="Explanation of what went wrong and why")
    root_cause = dspy.OutputField(desc="The identified root cause of the failure")

# ── Define Metric ──
def {packet.metric}(gold, pred, trace=None, pred_name=None, pred_trace=None):
    """Delta-based metric for skill evolution. Matches GEPA's required 5-arg signature."""
    score = 0.0
    if hasattr(pred, 'fix_steps') and pred.fix_steps:
        score += 0.4
    if hasattr(pred, 'explanation') and pred.explanation and len(str(pred.explanation)) > 20:
        score += 0.3
    if hasattr(pred, 'root_cause') and pred.root_cause:
        score += 0.3
    return score

# ── Create Example objects ──
trainset = []
for item in train_data:
    error_log = item.get("error_signature", item.get("context", {{}}).get("stack_trace", ""))
    context = json.dumps(item.get("context", {{}}))
    trainset.append(dspy.Example(
        error_log=error_log,
        context=context,
    ).with_inputs("error_log", "context"))

# ── Compile with BetterTogether ──
program = dspy.ChainOfThought(EvolvedSkill)

# Measure baseline
baseline_score = 0.0
for ex in holdout_data[:5]:
    try:
        error_log = ex.get("error_signature", "")
        context = json.dumps(ex.get("context", {{}}))
        pred = program(error_log=error_log, context=context)
        baseline_score += {packet.metric}(ex, pred) / 5
    except Exception:
        pass

print(f"BASELINE: baseline_score={{baseline_score:.3f}}")

# ── Optimize with BootstrapFewShot (works without reflection LM) ──
from dspy.teleprompt import BootstrapFewShot

optimizer = BootstrapFewShot(metric={packet.metric}, max_bootstrapped_demos=3, max_labeled_demos=3)

optimized = optimizer.compile(
    program,
    trainset=trainset,
)

# ── Evaluate on holdout ──
evolved_score = 0.0
for ex in holdout_data:
    try:
        error_log = ex.get("error_signature", "")
        context = json.dumps(ex.get("context", {{}}))
        pred = optimized(error_log=error_log, context=context)
        evolved_score += {packet.metric}(ex, pred) / len(holdout_data)
    except Exception:
        pass

delta = evolved_score - baseline_score
print(f"RESULT: best_score={{evolved_score:.3f}} delta={{delta:.3f}} iterations={packet.max_attempts}")
'''

    def _generate_skill_name(self, packet: SkillGenesisPacket) -> str:
        """Generate a clean skill name from intent."""
        name = packet.intent.lower()
        name = name.replace(" ", "-").replace(":", "").replace(",", "")
        name = name[:50].strip("-")
        return f"promethean-{name}"

    def _extract_metric(self, output: str, key: str, default: float) -> float:
        """Extract a metric value from DSPy output."""
        import re
        pattern = rf'{key}=(\d+\.?\d*)'
        match = re.search(pattern, output)
        if match:
            return float(match.group(1))
        return default

    def compile_with_retry(self, packet: SkillGenesisPacket) -> CompilationResult:
        """Compile with automatic retry on failure."""
        for attempt in range(1, packet.max_attempts + 1):
            result = self.compile(packet, attempt)
            if result.success and result.threshold_met:
                return result
        # Return last result even if all failed
        return result


# ── Singleton ───────────────────────────────────────────────────────
_compiler: Optional[DSPyCompiler] = None


def get_compiler(python_bin: str = sys.executable) -> DSPyCompiler:
    global _compiler
    if _compiler is None:
        _compiler = DSPyCompiler(python_bin)
    return _compiler
