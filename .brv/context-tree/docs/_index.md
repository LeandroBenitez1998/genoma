---
children_hash: a71d4119e388f6f696c270fd1202587c41019b22b842e94859adf7c2d81eff99
compression_ratio: 0.5456349206349206
condensation_order: 2
covers: [api/_index.md]
covers_token_total: 504
summary_level: d2
token_count: 275
type: summary
---
# docs/api — Hermes API Specification

## Architecture
OpenAPI 3.0 contract between Next.js frontend and FastAPI backend. Backend runs at `http://127.0.0.1:8000` (configurable via `NEXT_PUBLIC_API_BASE`).

## Endpoints

| Group | Methods |
|-------|---------|
| Skills | `GET /api/skills`, `GET /api/skills/{name}`, `GET /api/skills/{name}/evolution-history` |
| Evolution | `GET /api/evolution/runs`, `POST /api/evolution/start` |
| Jobs | `GET /api/jobs`, `GET /api/jobs/{jobId}`, `DELETE /api/jobs/{jobId}`, `GET /api/jobs/{jobId}/logs` |
| Health | `GET /api/health` |
| Realtime | `/ws` |

## Key Schemas

**EvolutionJob lifecycle:** `queued → loading_skill → building_dataset → validating → configuring → optimizing → evaluating → saving → completed/failed`

**ApiError kinds:** `network`, `timeout`, `server` (5xx), `client` (4xx)

**EvolutionRun:** tracks `baseline_score`, `evolved_score`, `improvement`, `constraints_passed`

## Drill-down
- Full spec: `hermes_api_openapi_specification.md`
- Backend: `backend/main.py`, `backend/job_tracker.py`
- Frontend client: `frontend/src/lib/api.ts`