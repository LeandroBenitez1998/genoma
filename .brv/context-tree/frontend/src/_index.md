---
children_hash: 39a72abd03573b8a0595d756d5ed750559bca3cddd7d080af1f7d84354e25316
compression_ratio: 0.19980787704130643
condensation_order: 1
covers: [components/_index.md, context.md, functioncallingpage.md, lib/_index.md, page.md, settingspage.md, sidebar.md]
covers_token_total: 5205
summary_level: d1
token_count: 1040
type: summary
---
## Frontend Component Structure

This group documents the core `src/components/` and `src/app/` presentation layer for the Hermes dashboard, centered on a shared page shell, navigation, and a small set of interactive UI components. The main architectural pattern is client-side React with animated Framer Motion transitions, Tailwind-style utility classes, and lazy-loaded page content in `src/app/page.tsx`.

### Layout and navigation

- **`sidebar.md`** defines the primary dashboard navigation. It exports the `Page` union (`overview`, `skills`, `evolution`, `datasets`, `memory`, `metrics`, `logs`, `settings`) and renders a collapsible, sticky left sidebar with icon-labeled nav items, active-state styling, animated label visibility, and width transitions between `240` and `64`.
- **`page.md`** is the top-level `Home` page shell in `src/app/page.tsx`. It maps `Page` values to dynamically imported components and renders them beside `Sidebar`, keeping page selection in local state.
- Together, `page.md` and `sidebar.md` establish the dashboard’s navigation contract: the sidebar drives page state, and `Home` resolves the active page into the corresponding lazily loaded view.

### Interaction and configuration components

- **`apiconfigcard.md`** documents `components/ApiConfigCard.tsx`, an animated glass-card for API endpoint configuration. It manages `OPENAI_API_KEY`, `NOUS_API_KEY`, and `OLLAMA_ENDPOINT`, with masked/unmasked toggles, per-field connection testing, and simulated success/error states.
- **`clickspark.md`** documents `components/bits/ClickSpark.tsx`, a reusable click-feedback wrapper that draws animated spark particles on a canvas overlay. It is generic enough to wrap arbitrary children and handles sizing, spark tracking, and animation with `ResizeObserver` and `requestAnimationFrame`.

### Page implementations and app composition

- **`settingspage.md`** covers `src/components/pages/SettingsPage.tsx`. This page surfaces system paths and environment variables, calls `fetchHealth()` on mount, shows Hermes repo and evolution engine paths plus skill counts, and allows toggling visibility of env values.
- **`functioncallingpage.md`** is a preserved stub for `src/components/pages/FunctionCallingPage.tsx`. The content indicates the page has been removed and should be replaced by `page.tsx` for available pages.
- **`page.md`** also reveals the page registry used by the app shell: `OverviewPage`, `SkillStudioPage`, `EvolutionPage`, `DatasetPage`, `MemoryPage`, `MetricsPage`, `LogsPage`, and `SettingsPage`, with loading placeholders for each dynamic import.

### Shared frontend patterns

- Client-side rendering is used throughout via `"use client"`.
- Motion/animation is a consistent UI pattern across the component set.
- The dashboard is themed for dark/light modes and uses utility-first styling with glass-card surfaces.
- The navigation model is strongly typed through the shared `Page` union exported from `sidebar.md` and consumed by `page.md`.

### API client foundation

- **`lib/_index.md`** summarizes `src/lib/api.ts` as the typed API client for the frontend. It provides React Query-compatible server-state access, typed endpoints for jobs, skills, evolution, datasets, metrics, and health checks, plus WebSocket streaming support.
- Key resilience decisions in `api_client_library.md` include `AbortController` timeouts, typed `ApiError` kinds (`network`, `timeout`, `server`, `client`), one-time token refresh on `401`, and WebSocket auto-reconnect after `3s`.
- The client authenticates with `X-Hermes-Session-Token` and falls back to `http://127.0.0.1:9119` when `NEXT_PUBLIC_API_BASE` is unset.

### Drill-down map

- See **`sidebar.md`** for the complete navigation model and `Page` union.
- See **`page.md`** for the dynamic page registry and shell composition.
- See **`settingspage.md`** for environment and health display logic.
- See **`apiconfigcard.md`** for API endpoint configuration UI behavior.
- See **`clickspark.md`** for the reusable click animation wrapper.
- See **`lib/_index.md`** and **`api_client_library.md`** for the typed API client architecture and endpoint surface.