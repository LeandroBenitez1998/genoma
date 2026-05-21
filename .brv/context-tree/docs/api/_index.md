---
children_hash: 50c773b90f6937381a937265ca7c7ce8090632fd257e370e2bd838288f3232dd
compression_ratio: 0.12634643377001456
condensation_order: 1
covers: [context.md, hermes_api_openapi_specification.md]
covers_token_total: 3435
summary_level: d1
token_count: 434
type: summary
---
# docs/api — API Specification Domain

## Overview
OpenAPI 3.0 specification documenting the Hermes backend API contract. Next.js frontend consumes these endpoints; FastAPI/Python backend exposes them at `http://127.0.0.1:8000` (overridable via `NEXT_PUBLIC_API_BASE`).

## Endpoint Groups

### Skills
- `GET /api/skills` — List all installed skills
- `GET /api/skills/{name}` — Get skill detail (frontmatter + body)
- `GET /api/skills/{name}/evolution-history` — Get evolution history for skill

### Evolution
- `GET /api/evolution/runs` — List all evolution runs
- `POST /api/evolution/start` — Start evolution job (`skill_name`, `iterations` 1-20, `eval_source`)

### Jobs
- `GET /api/jobs` — List jobs (optional `active_only` filter)
- `GET /api/jobs/{jobId}` — Get job detail
- `DELETE /api/jobs/{jobId}` — Cancel active job
- `GET /api/jobs/{jobId}/logs` — Get paginated logs (`since` param)

### Health
- `GET /api/health` — Returns `status`, `hermes_repo_exists`, `evolution_dir_exists`, `skills_count`, `categories`

### WebSocket
- `/ws` — Real-time job progress streaming

## Key Schemas

**EvolutionJob status flow:** `queued → loading_skill → building_dataset → validating → configuring → optimizing → evaluating → saving → completed/failed`

**ApiError** — Typed error contract with `kind` enum:
- `network` — Service unreachable
- `timeout` — Request timeout exceeded
- `server` — HTTP 5xx
- `client` — HTTP 4xx

**EvolutionRun** — Records `baseline_score`, `evolved_score`, `improvement`, `constraints_passed` per run

## Related Entries
- See `hermes_api_openapi_specification.md` for full OpenAPI YAML
- Backend implementation: `backend/main.py`, `backend/job_tracker.py`
- Frontend client: `frontend/src/lib/api.ts`