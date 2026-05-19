---
children_hash: 12f1830600dd1d745816e9834ba900a01ae72ef7e912baf47f5fecd1d9fa273f
compression_ratio: 0.4008097165991903
condensation_order: 2
covers: [backend/_index.md]
covers_token_total: 494
summary_level: d2
token_count: 198
type: summary
---
# Backend Domain Summary

FastAPI backend bridging Next.js frontend to hermes-agent-self-evolution system.

## Core Modules

- **init** — Empty module placeholder
- **job_tracker** — Persistent job tracking with JobStatus enum (10 states), EvolutionJob dataclass, JobTracker class managing lifecycle and log parsing via regex
- **main** — FastAPI app with ~20 endpoints + WebSocket for skills, evolution, jobs, datasets, and graph visualization
- **requirements** — Dependencies: fastapi>=0.115.0, uvicorn[standard]>=0.34.0, websockets>=13.0, pyyaml>=6.0

## Key Relationships

`main.py` imports `job_tracker` module (singleton tracker). Both modules reference HERMES_AGENT_REPO and EVOLUTION_DIR paths. Job tracker provides real-time progress parsing for evolution streaming via WebSocket.