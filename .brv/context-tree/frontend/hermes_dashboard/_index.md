---
children_hash: 2a0eeec8b2611fa8c30ac9d0157ba64605dba789be71603dd58b1a5ae9e6bd30
compression_ratio: 0.06735294117647059
condensation_order: 1
covers: [architecture_overview.md, globals.md, hermes_dashboard_frontend.md, layout.md, page.md, route.md]
covers_token_total: 17000
summary_level: d1
token_count: 1145
type: summary
---
# Hermes Dashboard Frontend

The curated entries describe the Next.js frontend for the Hermes/Genoma dashboard and its supporting UI layers. The overall app is a **Next.js 16** frontend connected to a **FastAPI backend on port 8000**, with the frontend on **port 3000**. The architecture emphasizes performance and a polished theme system: **Three.js was removed in favor of CSS gradients**, the backend is **lazy-loaded**, and `next.config` is set to **standalone**. See **Architecture Overview** for the top-level system shape and deployment implications.

## Core frontend shell and routing

The app uses the **Next.js app router** with a shared shell around page-level content. The root layout wires together:

- `Inter` and `Geist Mono` fonts
- `TooltipProvider`
- `ReactQueryProvider`
- `ThemeAwareBackground`
- global styles from `app/globals.css`

It also injects an early script to restore the dark theme from `localStorage` (`genoma-theme`) or system preference before hydration. See **Layout** for the root shell and theme bootstrap logic.

The main page acts as a simple router over app sections via `AppSidebar`, with a fixed `AnimatedThemeToggler` in the top-right corner. The active pages currently include:

- `overview`
- `skills`
- `evolution`
- `datasets`
- `metrics`
- `logs`
- `settings`
- `curator`

See **Hermes Dashboard Frontend** for the page inventory and routing structure.

## Global styling and design system

`app/globals.css` defines the **Genoma design system** and Tailwind v4 theme mapping. It establishes:

- brand tokens for **primary navy** (`#002444`) and **secondary rust orange** (`#a93800`)
- warm off-white backgrounds
- light/dark theme token sets
- sidebar color tokens
- chart palette tokens
- radius scale and typography mappings
- shared utility classes such as:
  - `.glass-card`
  - `.gradient-text`
  - `.led-pulse`
  - `.cursor-blink`
  - `.editorial-shadow`
  - `.glass-header`
  - `.genoma-cta`
  - `.genoma-input`

It also includes scrollbar styling, dark theme overrides, and base Tailwind application to body/html. See **Globals** for the full token set and visual language.

## Skills and evolution views

The **Skills page** is a provider-oriented skill management interface. It fetches skill providers through `@/lib/api`, supports:

- search across name/description/tags
- filtering by provider, status, and category
- toggling skill enabled state
- deleting a skill from one provider
- deleting a skill globally
- grouped provider cards with counts and metadata

It knows the main providers: **Claude Code**, **OpenCode**, **Kilocode**, **Antigravity**, and **Hermes**. The empty state points to provider skill directories such as `~/.claude/skills/` and `~/.hermes/skills/`. See **Page** for the full skill hub behavior.

The **Evolution Hub** is a separate multi-provider skill evolution dashboard. It combines current evolvable skills and historical evolution runs, with:

- provider tabs
- skill search
- evolution stats
- evolution/re-evolution actions
- polling for active jobs
- a diff modal for before/after comparison
- a history table showing baseline, evolved score, delta, elapsed time, and pass/fail constraint status

Its flow is: fetch evolvable skills and runs → start evolution job → poll until complete → refresh runs → inspect diffs. See **Page** for the full implementation and comparison workflow.

## API proxy and session token handling

The frontend uses an API route layer to proxy requests to the FastAPI backend. The catch-all route at `app/api/auth/token/route.ts` forwards most `/api/*` traffic to `http://127.0.0.1:8000`, preserving request method, headers, and body while stripping the host header. It also forwards the `x-hermes-session-token` header when present and returns a 503 with a backend-unreachable message if the backend cannot be reached.

A second handler in the same file fetches the server HTML and extracts `__HERMES_SESSION_TOKEN__` from the page source so the browser can obtain the token without CORS issues. See **Route** for the proxy semantics and token retrieval behavior.

## Key relationships and drill-down map

- **Architecture Overview** — top-level Next.js/FastAPI architecture, lazy loading, CSS gradient replacement
- **Hermes Dashboard Frontend** — page structure and app-router composition
- **Layout** — root app shell, fonts, theme bootstrap, providers
- **Globals** — design tokens, Tailwind theme mapping, shared CSS utilities
- **Page** — skill management and evolution UI implementation
- **Route** — backend proxying and session token acquisition