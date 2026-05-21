---
children_hash: 48aff4df02a4e090fa5f912bdd2ee56a0c5dbb6e0c894f85b2a02929cae9408c
compression_ratio: 0.8106734434561627
condensation_order: 2
covers: [api/_index.md]
covers_token_total: 787
summary_level: d2
token_count: 638
type: summary
---
# docs/api — Hermes Agent API Contract

## Scope
`docs/api` captures the Hermes agent self-evolution backend contract and how the dashboard integrates with it. The core concerns are skills management, evolution runs, job control, health checks, typed errors, and disconnected-state handling.

## Primary source: `hermes_api_openapi_specification.md`
This is the canonical Hermes API specification for the dashboard and agent gateway. It is an OpenAPI 3.1 contract covering:

- `GET /api/skills`
- `GET /api/skills/{name}`
- `GET /api/skills/{name}/evolution-history`
- `GET /api/evolution/runs`
- `POST /api/evolution/start`
- `GET /api/jobs`
- `GET /api/jobs/{jobId}`
- `DELETE /api/jobs/{jobId}`
- `GET /api/jobs/{jobId}/logs`
- `GET /api/health`

It defines reusable schemas for `SkillInfo`, `SkillDetail`, `EvolutionRun`, `EvolutionJob`, `ApiError`, and `HealthStatus`.

### Key architectural rules
- `503 ServiceUnavailable` is standardized so the frontend can map backend outages to a **“Desconectado”** state with retry behavior.
- `NEXT_PUBLIC_API_BASE` is the explicit override point for frontend backend targeting.
- All non-2xx and network failures are mapped through `ApiError`.
- `/api/health` is the backend health source of truth.
- `HealthStatus` supports a disconnected fallback model with `lastSeen`.

### Flow and structure
The API models the evolution lifecycle end-to-end:
skill selection → evolution run → job execution → job logs → skill evolution history.

The contract is organized into separate groups:
- skill endpoints
- evolution endpoints
- job endpoints
- health endpoint

The design favors typed JSON responses and reusable component schemas. Job logs support pagination/streaming via `since`, and job status follows a finite lifecycle:

`queued -> loading_skill -> building_dataset -> validating -> configuring -> optimizing -> evaluating -> saving -> completed/failed`

## Supporting entry: `context.md`
`context.md` is the older broad overview for `api`. It covers the same general domain at a higher level, including job management, skills registry, evolution endpoints, WebSocket streaming, and configuration management. Use it as a broad entry point, but prefer the OpenAPI specification for exact endpoint and schema details.

## Consolidation note
`hermes_api_specification.md` was consolidated into `hermes_api_openapi_specification.md` because both described the same Hermes API contract. The OpenAPI 3.1 file is now the preferred source for endpoint definitions, schema contracts, and error-handling behavior.