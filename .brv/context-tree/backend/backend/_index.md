---
children_hash: fa7fc518cdde3800a2beb0727fae728f6acd2a999b0fe58a86d5d01fc641ca17
compression_ratio: 0.02604840199519675
condensation_order: 1
covers: [init.md, job_tracker.md, main.md, requirements.md]
covers_token_total: 16239
summary_level: d1
token_count: 423
type: summary
---
# Backend Domain Summary

The Backend domain contains the hermes-dashboard FastAPI backend modules that bridge the Next.js frontend to the hermes-agent-self-evolution system.

## Entry Overview

- **[init.md](backend/backend/init.md)** — Empty Python module placeholder

- **[job_tracker.md](backend/backend/job_tracker.md)** — Persistent job tracking system for evolution runs
  - **JobStatus** enum: 10 states (QUEUED → COMPLETED/FAILED)
  - **EvolutionJob** dataclass: tracks skill_name, iterations, progress, scores, logs
  - **JobTracker** class: manages job lifecycle, parses log output via PHASE_PATTERNS, SCORE_PATTERN, ITER_PATTERN regex
  - Persists logs to `~/.hermes/evolution-logs/`

- **[main.md](backend/backend/main.md)** — FastAPI application with ~20 REST endpoints + WebSocket
  - **Skill endpoints**: list providers, refresh, toggle, delete, get content
  - **Evolution endpoints**: start run, list runs, history, diff, metrics
  - **Job endpoints**: list, get, get logs, cancel
  - **Dataset endpoints**: list, get, import sessions
  - **Graph endpoint**: generates vis.js format from skills, memory, and evolution runs (with community detection)
  - **Metrics & constraints validation**
  - Uses Ollama when available, falls back to cloud providers

- **[requirements.md](backend/backend/requirements.md)** — Dependencies: fastapi>=0.115.0, uvicorn[standard]>=0.34.0, websockets>=13.0, pyyaml>=6.0

## Key Relationships

- `main.py` imports and uses `job_tracker` module (tracker singleton, JobStatus, EvolutionJob)
- Both modules reference HERMES_AGENT_REPO and EVOLUTION_DIR paths
- Job tracker provides real-time progress parsing for evolution streaming via WebSocket