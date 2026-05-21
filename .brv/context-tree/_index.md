---
children_hash: 380f420e01d921a7e0a8ac009385af73640a4fc05effe2c1da4a110c873b4a42
compression_ratio: 0.7318802521008403
condensation_order: 3
covers: [backend/_index.md, docs/_index.md, frontend/_index.md, meta/_index.md, src/_index.md]
covers_token_total: 3808
summary_level: d3
token_count: 2787
type: summary
---
# Structural Overview: Backend, Docs API, Frontend, Meta, and Shared UI

## Repository-level shape
- The curated knowledge splits into five major areas:
  - **Backend**: FastAPI backend, collectors, evaluation, orchestration, and storage.
  - **docs/api**: Canonical Hermes API contract and frontend/backend integration rules.
  - **Frontend**: Next.js 16 dashboard app, routing shell, proxy bridge, and UI composition.
  - **Meta**: Curation workflow tracking and root project configuration.
  - **src**: Shared frontend UI components and client utilities.

## Backend cluster
The backend knowledge forms an end-to-end evolution pipeline centered on **source → analysis → curated knowledge**, with **CanonicalRun** and job metadata as the common glue across ingestion, tracking, and storage.

### Main backend application
- **backend/_index.md**
  - Core backend is the **`hermes-dashboard` FastAPI backend** bridging the Next.js frontend to the **`hermes-agent-self-evolution`** system.
  - Key modules:
    - `init.md` — empty placeholder
    - `job_tracker.md` — persistent job tracking for evolution runs
    - `main.md` — FastAPI app with ~20 REST endpoints plus a WebSocket
    - `requirements.md` — runtime dependencies (`fastapi`, `uvicorn[standard]`, `websockets`, `pyyaml`)
  - Shared environment references: `HERMES_AGENT_REPO`, `EVOLUTION_DIR`.

- **job_tracker.md**
  - Models evolution lifecycle via `JobStatus` with 10 states from `QUEUED` to `COMPLETED/FAILED`.
  - `EvolutionJob` tracks `skill_name`, `iterations`, `progress`, `scores`, and logs.
  - Uses regex parsing for streamed logs via `PHASE_PATTERNS`, `SCORE_PATTERN`, and `ITER_PATTERN`.
  - Logs persist to `~/.hermes/evolution-logs/`.

- **main.md**
  - Primary backend surface.
  - Exposes skill endpoints, evolution endpoints, job endpoints, dataset endpoints, graph generation, and validation/metrics routes.
  - Graph output is `vis.js`-compatible and includes skills, memory, evolution runs, and community detection.
  - Uses Ollama when available, otherwise cloud providers.

### Ingestion and normalization
- **collectors/_index.md**
  - Collector layer normalizes session and trace data into the shared **CanonicalRun** schema.

- **Claude Code Collector**
  - Converts Claude Code session JSONL logs into `CanonicalRun`.
  - Default source root: `~/.claude/projects`.
  - Extracts `run_id`, `task_name`, `started_at`, `ended_at`, `model`, `repo`, `tool_calls`, `metrics`, `errors`, and `context.cwd`.
  - `collect_all(project_path=None, limit=50)` recursively scans `.jsonl` files and skips malformed sessions.
  - Outcome inference is heuristic: system errors → `partial`/`failure`; assistant `stop_reason == "end_turn"` → `success`; otherwise `unknown`.

- **Hermes Collector**
  - Wraps `TraceIngestor` and converts `TraceRecord` data into `CanonicalRun`.
  - Main methods: `collect_from_trace(trace)`, `collect_batch(traces)`, `load_from_disk(limit=100)`, `get_run_by_id(run_id)`.
  - Skips malformed trace files during loading.

### Evaluation
- **eval/_index.md**
  - Backend scoring pipeline for traces and generated dataset evaluation.
  - Core implementation: `backend/eval/engine.py`.

### Promethean orchestration
- **promethean/_index.md**
  - Orchestration layer centered on `backend/promethean/cycle_orchestrator.py`.
  - Coordinates iterative evolution and skill deployment above the runtime/deployment flow.

### Storage
- **storage/_index.md**
  - Persistence layer for execution metadata.
  - Main implementation: `backend/storage/run_store.py`.
  - Focuses on SQL schema plus run storage helpers for retrieval and analysis.

### Cross-cutting backend flow
- **Collectors** normalize raw inputs into `CanonicalRun`.
- **JobTracker** turns streamed evolution output into persistent lifecycle states.
- **Run store** persists execution metadata.
- **Promethean** coordinates iterative evolution and deployment.
- The whole backend cluster supports an **end-to-end UI → API → job tracking → persistence** evolution workflow.

## docs/api cluster
The API documentation defines the Hermes backend contract and the frontend integration rules.

- **docs/_index.md**
  - Scope: skills management, evolution runs, job control, health checks, typed errors, and disconnected-state handling.

- **hermes_api_openapi_specification.md** is the canonical contract.
  - OpenAPI 3.1 endpoints:
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
  - Shared schemas: `SkillInfo`, `SkillDetail`, `EvolutionRun`, `EvolutionJob`, `ApiError`, `HealthStatus`.

### Key API rules
- `503 ServiceUnavailable` maps to frontend **“Desconectado”** state with retry behavior.
- `NEXT_PUBLIC_API_BASE` is the explicit frontend override for backend targeting.
- All network/non-2xx failures flow through `ApiError`.
- `/api/health` is the health source of truth.
- `HealthStatus` supports disconnected fallback via `lastSeen`.

### Lifecycle structure
- The API models the evolution chain:
  - skill selection → evolution run → job execution → job logs → skill evolution history
- Job status follows:
  - `queued -> loading_skill -> building_dataset -> validating -> configuring -> optimizing -> evaluating -> saving -> completed/failed`

### Supporting context
- **context.md** provides a broader, older overview of the same domain, including job management, skills registry, evolution endpoints, WebSocket streaming, and configuration management.
- `hermes_api_specification.md` was consolidated into the OpenAPI file and is now secondary.

## Frontend cluster
The frontend is a **Next.js 16 App Router** dashboard paired with a **FastAPI backend on port 8000** and frontend on **port 3000**. Its dominant patterns are a **shared theme-aware shell**, **lazy-loaded page composition**, and a clean Genoma design system.

### App shell and architecture
- The app uses a consistent root shell with:
  - `Inter`, `Geist Mono`
  - `TooltipProvider`
  - `ReactQueryProvider`
  - `ThemeAwareBackground`
  - global styles from `app/globals.css`
- Dark theme bootstrapping reads `localStorage` key `genoma-theme` or system preference before hydration.
- `next.config` is set to `standalone`.
- Three.js was removed in favor of CSS gradients for performance and simpler theming.

### Routing and page composition
- `src/app/page.tsx` keeps page selection in local state and resolves into lazily imported views.
- Active page areas include:
  - `overview`
  - `skills`
  - `evolution`
  - `datasets`
  - `metrics`
  - `logs`
  - `settings`
  - `curator`
  - `memory` is also referenced in component-layer summaries
- The app uses a sidebar-driven shell across routing layers.

### Design system and global styling
- `app/globals.css` defines the Genoma design system and Tailwind v4 token mapping.
- Core brand colors:
  - primary navy `#002444`
  - secondary rust orange `#a93800`
- Shared utility classes include:
  - `.glass-card`
  - `.gradient-text`
  - `.led-pulse`
  - `.cursor-blink`
  - `.editorial-shadow`
  - `.glass-header`
  - `.genoma-cta`
  - `.genoma-input`

### Skills and evolution interfaces
- The **Skills** page is a provider-oriented management UI using `@/lib/api`.
- It supports search/filtering, enabled-state toggling, and deleting skills globally or per provider.
- Providers referenced: **Claude Code**, **OpenCode**, **Kilocode**, **Antigravity**, **Hermes**.
- The **Evolution Hub** is a multi-provider evolution dashboard with provider tabs, stats, evolution/re-evolution actions, polling for active jobs, diff inspection, and history tracking.

### API proxying and session-token bridge
- The frontend proxies `/api/*` through a catch-all route to `http://127.0.0.1:8000`, preserving method, headers, and body while stripping the host header.
- The proxy forwards `x-hermes-session-token`.
- It returns `503` when the backend is unreachable.
- It also extracts `__HERMES_SESSION_TOKEN__` from server HTML so the browser can obtain the token without CORS issues.
- This is the transport/auth bridge between frontend and backend.

### Shared frontend component layer
- The component layer centers on reusable dashboard building blocks with client-side React, Framer Motion transitions, and utility-first styling.
- `sidebar.md` defines the typed `Page` union and a collapsible, sticky navigation shell.
- `page.md` maps page values to dynamically imported page components.
- Additional shared components:
  - `ApiConfigCard`
  - `ClickSpark`
  - `SettingsPage`
  - removed `FunctionCallingPage` stub

### Key frontend drill-down entries
- **Hermes Dashboard Frontend**
- **Session-token proxying is the frontend/backend bridge**
- **Frontend Component Structure**
- **The app uses a consistent lazy-loaded, theme-aware shell across routing layers**

## Meta cluster
Repository-wide meta knowledge covers curation workflow tracking and canonical project setup.

### Curation context
- **curation_context/_index.md**
  - Records empty or non-actionable curation attempts from RLM sessions.
  - `empty_context.md` captures inputs that only contained placeholders like `"."` and yielded no extractable facts.
  - Used to distinguish failed curation attempts from genuine content and avoid reprocessing empty inputs.

### Project configuration
- **project_config/_index.md**
  - Canonical entry for repository-wide configuration and tooling.
  - Root stack:
    - Next.js
    - TypeScript
    - ESLint
    - Tailwind
    - pnpm workspaces
    - shadcn/ui
  - Key config files:
    - `next.config.ts`
    - `tsconfig.json`
    - `eslint.config.mjs`
    - `postcss.config.mjs`
    - `pnpm-workspace.yaml`
    - `components.json`
    - `package.json`
  - Structural pattern: a single root configuration layer spanning build behavior, linting, workspace structure, and component tooling.
  - Flow: `config -> build -> lint -> component tooling`

## Shared src cluster
The `src` knowledge splits into reusable UI components and client utilities.

- **components/_index.md**
  - Shared Hermes dashboard building blocks for composition and interaction.
  - Covers `ApiConfigCard`, sidebar/navigation, theme controls, and animated UI bits.
  - Primary source: `src/components/ApiConfigCard.tsx`
  - Drill down: `reusable_ui_components.md`

- **lib/_index.md**
  - Frontend API helpers in `src/lib/api.ts`.
  - Includes the API client and query client helpers used by the frontend.
  - Drill down: `client_libraries.md`

## Main relationships to preserve
- **Backend** implements the runtime, ingestion, job tracking, evaluation, orchestration, and persistence layers.
- **docs/api** defines the contract the frontend and backend share.
- **Frontend** consumes the API, proxies session state, and presents evolution and skill management workflows.
- **Meta** captures both repository setup and curation hygiene.
- **src** provides shared UI and client infrastructure used by the frontend shell and pages.