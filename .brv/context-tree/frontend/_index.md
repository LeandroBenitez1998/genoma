---
children_hash: b745730749b5537914c951603ae6ee7ce77a03e9c36683052d01dd1db2c2372e
compression_ratio: 0.32056825200741196
condensation_order: 2
covers: [hermes_dashboard/_index.md, session-token-proxying-is-the-frontend-backend-bridge.md, src/_index.md, the-app-uses-a-consistent-lazy-loaded-theme-aware-shell-across-routing-layers.md]
covers_token_total: 3238
summary_level: d2
token_count: 1038
type: summary
---
## Frontend structural overview

This d2 set describes the Hermes dashboard frontend as a **Next.js 16 App Router** application with a **FastAPI backend on port 8000** and the frontend on **port 3000**. The system favors a **shared, theme-aware shell**, **lazy-loaded page composition**, and a polished visual layer built around the Genoma design system. Key drill-down entries are **Hermes Dashboard Frontend**, **Session-token proxying is the frontend/backend bridge**, **Frontend Component Structure**, and **The app uses a consistent lazy-loaded, theme-aware shell across routing layers**.

### App architecture and shell
- The frontend uses a consistent root shell with `Inter` and `Geist Mono`, `TooltipProvider`, `ReactQueryProvider`, `ThemeAwareBackground`, and global styles from `app/globals.css`.
- Dark theme bootstrapping is handled early via `localStorage` key `genoma-theme` or system preference before hydration.
- `next.config` is set to `standalone`, and Three.js was removed in favor of CSS gradients for performance and simpler theming.
- Drill down in **Hermes Dashboard Frontend** and **The app uses a consistent lazy-loaded, theme-aware shell across routing layers**.

### Routing and page composition
- The app router is organized around a shared sidebar-driven shell.
- `src/app/page.tsx` keeps page selection in local state and resolves it into lazily imported views.
- Active page areas include `overview`, `skills`, `evolution`, `datasets`, `metrics`, `logs`, `settings`, and `curator`; the component-layer summary also mentions `memory`.
- Drill down in **Frontend Component Structure** and **Hermes Dashboard Frontend** for the page registry and navigation contract.

### Design system and global styling
- `app/globals.css` defines the Genoma design system and Tailwind v4 token mapping.
- Core brand values include **primary navy `#002444`** and **secondary rust orange `#a93800`**, plus warm off-white backgrounds and dark/light token sets.
- Shared utility classes include `.glass-card`, `.gradient-text`, `.led-pulse`, `.cursor-blink`, `.editorial-shadow`, `.glass-header`, `.genoma-cta`, and `.genoma-input`.
- Drill down in **Globals** for the full token and styling model.

### Skills and evolution interfaces
- The **Skills page** is a provider-oriented skill management UI that fetches providers through `@/lib/api`, supports search/filtering, and allows toggling enabled state plus deleting skills globally or per provider.
- Main providers referenced are **Claude Code**, **OpenCode**, **Kilocode**, **Antigravity**, and **Hermes**.
- The **Evolution Hub** is a multi-provider skill evolution dashboard with provider tabs, stats, evolution and re-evolution actions, polling for active jobs, diff inspection, and history tracking.
- Drill down in **Hermes Dashboard Frontend** and **Frontend Component Structure** for the detailed workflows.

### API proxying and session-token bridge
- The frontend proxies `/api/*` traffic through a catch-all route to `http://127.0.0.1:8000`, preserving method, headers, and body while stripping the host header.
- The proxy forwards `x-hermes-session-token` and returns `503` when the backend is unreachable.
- The same route also extracts `__HERMES_SESSION_TOKEN__` from server HTML so the browser can obtain the token without CORS issues.
- This proxy pattern is the transport/auth bridge between the frontend and backend; drill down in **Session-token proxying is the frontend/backend bridge** and **Route**.

### Shared frontend component layer
- The component layer centers on reusable dashboard building blocks with client-side React, Framer Motion transitions, and utility-first styling.
- `sidebar.md` defines the typed `Page` union and a collapsible, sticky navigation shell.
- `page.md` maps page values to dynamically imported page components.
- Additional shared components include `ApiConfigCard` for API configuration, `ClickSpark` for click feedback, `SettingsPage` for environment and health display, and the removed `FunctionCallingPage` stub.
- Drill down in **Frontend Component Structure** for component-by-component behavior and API client foundations.