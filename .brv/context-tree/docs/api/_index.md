---
children_hash: 421c2efc31c5d9931665064358ef0f649a63c7531951255331ff493d99503ed0
compression_ratio: 0.17920519870032492
condensation_order: 1
covers: [context.md, hermes_api_openapi_specification.md]
covers_token_total: 4001
summary_level: d1
token_count: 717
type: summary
---
# docs/api — Hermes Agent API Contract

## Scope
The `docs/api` topic documents the Hermes agent self-evolution backend contract, centered on the OpenAPI specification and its frontend/backend integration rules. It covers skills management, evolution runs, job control, health checks, typed errors, and the standardized disconnected-state behavior used by the dashboard.

## Key entry: `hermes_api_openapi_specification.md`
- Canonical Hermes API specification for the dashboard and agent gateway.
- OpenAPI 3.1 document describing:
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
- Defines reusable schemas for `SkillInfo`, `SkillDetail`, `EvolutionRun`, `EvolutionJob`, `ApiError`, and `HealthStatus`.
- Standardizes `503 ServiceUnavailable` responses so the frontend can map backend unavailability to a “Desconectado” state with retry behavior.
- Explicitly ties frontend behavior to `NEXT_PUBLIC_API_BASE` override and to `ApiError` mapping for all non-2xx or network failures.

## Architectural relationships
- The frontend Next.js dashboard consumes this API contract directly.
- The Hermes CLI gateway exposes the contract over the FastAPI backend.
- `/api/health` acts as the backend health source of truth, while `HealthStatus` provides a disconnected fallback model with `lastSeen`.
- Evolution lifecycle is represented across runs, jobs, job logs, and skill evolution history, creating a connected flow from skill selection to execution and monitoring.

## Structural patterns
- Skill endpoints are grouped separately from evolution endpoints, job endpoints, and health.
- The API prefers typed JSON responses and reusable component schemas.
- Job logs are paginated/streamed via `since`, and job status is modeled as a finite lifecycle:
  `queued -> loading_skill -> building_dataset -> validating -> configuring -> optimizing -> evaluating -> saving -> completed/failed`

## Supporting entry: `context.md`
- Older broad topic overview for `api`.
- Summarizes the same general scope at a higher level: job management, skills registry, evolution endpoints, WebSocket streaming, and configuration management.
- Should be treated as the broader topic summary and cross-referenced to the newer OpenAPI specification.

## Related consolidation note
- `hermes_api_specification.md` was consolidated into `hermes_api_openapi_specification.md` because both described the same Hermes API contract.
- The richer OpenAPI 3.1 file is the preferred source for endpoint details, schema definitions, and error-handling rules.
- The abstract/overview companion files remain as supporting metadata for the merged specification.