---
children_hash: 389c2df13933c66ce0fe0315d13164eb36710f49e971334300a4c3927b66c30b
compression_ratio: 0.5270618556701031
condensation_order: 2
covers: [hermes_dashboard/_index.md, src/_index.md]
covers_token_total: 776
summary_level: d2
token_count: 409
type: summary
---
# Hermes Dashboard

## Architecture

Next.js 16 frontend ↔ FastAPI backend, communicating across ports 3000 and 8000 (env-configured as `NEXT_PUBLIC_API_BASE` → `http://127.0.0.1:9119`).

**Stack:** Next.js 16 · React Query · Framer Motion · CSS gradients (Three.js removed for lighter footprint)

## Frontend Structure

**8 Navigation Sections** (sidebar.md): Overview · Skills · Evolution · Datasets · Memory · Metrics · Logs · Settings

All pages lazy-loaded via `next/dynamic` with loading states.

**Key Components:**
- `Sidebar` — Collapsible (64px/240px), Framer Motion animations, cyan accent, dual light/dark mode
- `SettingsPage` — System paths, env vars (`OPENAI_API_KEY`, `HERMES_AGENT_REPO`), health status

**API Client** (`lib/api.ts`, `api_client_library.md`):
- Auth: `X-Hermes-Session-Token` header, lazy-loaded session
- Resilience: 15s AbortController timeouts, 401 retry with token refresh, WebSocket 3s auto-reconnect
- Types: `SkillInfo`, `SkillDetail`, `EvolutionJob`, `EvolutionRun`, `MetricsData`, `DatasetInfo`

## Source Files

| Layer | Files |
|-------|-------|
| Pages | `src/app/page.tsx`, `src/app/layout.tsx` |
| Components | `src/components/Sidebar.tsx`, `src/components/pages/*.tsx` |
| API | `src/lib/api.ts` |
| Backend | `backend/main.py` (FastAPI, ~20 endpoints + WebSocket) |

## Drill-Down References

- `hermes_dashboard/architecture_overview.md` — Full architecture details
- `src/components/sidebar_navigation_component.md` — Sidebar implementation
- `src/lib/api_client_library.md` — API client specification
- `src/page.md` / `src/sidebar.md` / `src/settingspage.md` — Individual page docs