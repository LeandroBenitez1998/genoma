# Hermes Evolution Dashboard — Backend Overview

## Key Points

- **FastAPI Backend**: Bridges Next.js frontend to hermes-agent-self-evolution Python modules with REST + WebSocket support
- **Skill Registry Integration**: Manages skill providers, tracks global/provider-level skills, handles enable/disable and deletion
- **Evolution Run Tracking**: Lists runs from `metrics.json` files and job tracker, normalizes metrics across different evolve script versions (`evolve_skill.py` vs `evolve_now.py`)
- **Python Version Detection**: `_find_python()` locates suitable Python executable (prefers 3.12 with dspy installed)
- **8 API Endpoints** for skill management and evolution monitoring
- **6 Pydantic Models**: `SkillInfo`, `EvolveRequest`, `MemoryEntry`, `RunMetrics`, `ToggleSkillRequest`, `ConnectionManager`

## Structure / Sections Summary

| Section | Description |
|---------|-------------|
| **Imports & Dependencies** | FastAPI, Pydantic, asyncio, JSON, pathlib, subprocess, dotenv |
| **Paths** | `HERMES_REPO`, `EVOLUTION_DIR`, `SKILLS_DIR`, `MEMORY_DIR` — resolves via env vars or conventional locations |
| **Classes** | `ConnectionManager` (WebSocket), 5 Pydantic request/response models |
| **Helper Functions** | `_find_python()`, `_normalize_metrics()`, `_find_skill_file()`, `_parse_skill_content()` |
| **SKILLS Endpoints** | Provider listing, skill toggling, global/provider skill deletion, skill content retrieval |
| **EVOLUTION Endpoints** | List all runs, skill-specific history, baseline vs evolved diff |

## Notable Entities & Patterns

- **Environment Variables**: `HERMES_AGENT_REPO`, `EVOLUTION_DIR`, `PYTHON`
- **Path Resolution Pattern**: Env var → sibling directory → home directory fallback
- **Metrics Normalization**: Supports multiple evolve script output formats (unifies `skill`/`skill_name`, `original_size`/`baseline_score`, etc.)
- **WebSocket Broadcasting**: `ConnectionManager` class manages real-time client connections
- **Job Tracker Integration**: Imports `tracker`, `EvolutionJob`, `JobStatus` from `.job_tracker`
- **Skill Registry**: Imports `get_registry` from `.skill_registry` for provider/skill management