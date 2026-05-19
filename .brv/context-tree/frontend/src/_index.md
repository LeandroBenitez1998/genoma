---
children_hash: 90692b63a08a05d9811e0d3979c4a61bc3467fb2063e5c3b3eb75018971bdcc6
compression_ratio: 0.09087154068566708
condensation_order: 1
covers: [components/_index.md, context.md, functioncallingpage.md, lib/_index.md, page.md, settingspage.md, sidebar.md]
covers_token_total: 4842
summary_level: d1
token_count: 440
type: summary
---
# Frontend Architecture (src)

## Overview
Next.js frontend with lazy-loaded page components, React Query for server state, and Framer Motion animations. Connects to FastAPI backend via typed API client.

## Page Structure

**8 Navigation Sections** (see `sidebar.md` for full nav):
| Page | Component | Purpose |
|------|-----------|---------|
| Overview | `OverviewPage` | Dashboard home |
| Skills | `SkillStudioPage` | Skill management |
| Evolution | `EvolutionPage` | Evolution engine control |
| Datasets | `DatasetPage` | Dataset analysis |
| Memory | `MemoryPage` | Memory/intelligence |
| Metrics | `MetricsPage` | Analytics & metrics |
| Logs | `LogsPage` | Live log streaming |
| Settings | `SettingsPage` | System paths & env vars |

All pages lazy-loaded via `next/dynamic` with loading states.

## Key Components

- **`Sidebar`** — Collapsible (64px/240px), animated via Framer Motion, cyan accent theme, dual light/dark mode
- **`SettingsPage`** — Displays system paths, env vars (OPENAI_API_KEY, HERMES_AGENT_REPO), health status via `fetchHealth()`

## API Client (`lib/api.ts`)

See `lib/_index.md` and `api_client_library.md` for full details.

**Resilience:** 15s AbortController timeouts, retry on 401 with token refresh, WebSocket 3s auto-reconnect

**Auth:** `X-Hermes-Session-Token` header, lazy-loaded session

**Env:** `NEXT_PUBLIC_API_BASE` → `http://127.0.0.1:9119`

**Key Types:** `SkillInfo`, `SkillDetail`, `EvolutionJob`, `EvolutionRun`, `MetricsData`, `DatasetInfo`, `ConstraintResult`, `ProviderSummary`

## Source Files
- `src/app/page.tsx` — Root page with page routing
- `src/components/Sidebar.tsx` — Navigation sidebar
- `src/components/pages/*.tsx` — Page components (lazy-loaded)
- `src/lib/api.ts` — Typed API client