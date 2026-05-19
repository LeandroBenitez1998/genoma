"""
Promethean Cycle — Ciclo de Hiper-Evolución Autónoma del Dashboard

Módulos:
  ① trace_ingestion  — PERCIBE: ingesta de trazas multi-agente
  ② gepa_strategist   — DIAGNOSTICA + FORMULA: GEPA strategic layer
  ③ dspy_compiler     — COMPILA: DSPy BetterTogether compilation
  ④ delta_validator   — VALIDA: holdout validation + delta
  ⑤ skill_deployer    — DESPLIEGA: auto-registro en skill registry
  ⑥ cycle_orchestrator — OBSERVA: full 7-phase orchestrator

El dashboard deja de ser espejo y se convierte en oráculo.
"""

__version__ = "1.0.0"
__all__ = [
    "models",
    "trace_ingestion",
    "gepa_strategist",
    "dspy_compiler",
    "delta_validator",
    "skill_deployer",
    "cycle_orchestrator",
]
