---
children_hash: 28dd785d82a778d1717dc864f2d77eefc970e447e4654c326b49c4865c35a44a
compression_ratio: 0.42490272373540855
condensation_order: 3
covers: [backend/_index.md, docs/_index.md, frontend/_index.md, meta/_index.md]
covers_token_total: 1285
summary_level: d3
token_count: 546
type: summary
---
# Hermes Dashboard — System Architecture

## Overview

Full-stack monitoring dashboard bridging Next.js frontend to hermes-agent-self-evolution via FastAPI backend.

## Architecture

```
Next.js (port 3000) ←→ FastAPI (port 8000, configurable)
                    ←→ WebSocket for real-time job streaming
```

## Frontend Layer

- **Stack:** Next.js 16 · React Query · Framer Motion · CSS gradients
- **8 Navigation Sections:** Overview · Skills · Evolution · Datasets · Memory · Metrics · Logs · Settings
- **API Client** (`frontend/src/lib/api.ts`): 15s timeouts, WebSocket 3s auto-reconnect, lazy-loaded session
- **Key Components:** `Sidebar` (collapsible 64px/240px, dual themes), `SettingsPage` (system paths, env vars)

## Backend Layer

- **Core Modules:** `job_tracker` (JobStatus enum, 10 states; EvolutionJob dataclass; log parsing via regex), `main` (~20 endpoints + WebSocket)
- **Dependencies:** fastapi>=0.115.0, uvicorn[standard]>=0.34.0, websockets>=13.0, pyyaml>=6.0
- **EvolutionJob lifecycle:** queued → loading_skill → building_dataset → validating → configuring → optimizing → evaluating → saving → completed/failed

## API Contract

| Group | Endpoints |
|-------|-----------|
| Skills | `GET /api/skills`, `GET /api/skills/{name}`, `GET /api/skills/{name}/evolution-history` |
| Evolution | `GET /api/evolution/runs`, `POST /api/evolution/start` |
| Jobs | `GET/DELETE /api/jobs/{jobId}`, `GET /api/jobs/{jobId}/logs` |
| Health | `GET /api/health` |

## Key Relationships

- Backend imports `job_tracker` singleton; both reference `HERMES_AGENT_REPO` / `EVOLUTION_DIR` paths
- Frontend lazy-loads all pages via `next/dynamic`; backend streams job progress via WebSocket
- `ApiError` kinds: `network`, `timeout`, `server` (5xx), `client` (4xx)

## Drill-Down

| Area | Source |
|------|--------|
| Full architecture | `frontend/hermes_dashboard/architecture_overview.md` |
| API specification | `docs/api/hermes_api_openapi_specification.md` |
| Sidebar implementation | `frontend/src/components/sidebar_navigation_component.md` |
| API client details | `frontend/src/lib/api_client_library.md` |
| Job tracking | `backend/job_tracker.md`, `backend/main.md` |