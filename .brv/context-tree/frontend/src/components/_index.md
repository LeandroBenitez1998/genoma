---
children_hash: 6644c0cc075f50f81fd403038b4fcef037b1be8b2ba02db43fea88c9c4ecda94
compression_ratio: 0.15199637023593465
condensation_order: 0
covers: [apiconfigcard.md, clickspark.md, sidebar_navigation_component.md]
covers_token_total: 4408
summary_level: d0
token_count: 670
type: summary
---
## Frontend Components Overview

This set documents three Next.js frontend components under `src/components/` and `src/components/bits/`, covering API configuration, click feedback animation, and dashboard navigation. The shared pattern across entries is client-side React with `use client`, Framer Motion for animation, and Tailwind-style utility classes for styling.

### ApiConfigCard
See **`apiconfigcard.md`** for the full implementation of `components/ApiConfigCard.tsx`.

- Renders an animated `glass-card` panel titled **API Configuration** with the subtitle **Configure your model endpoints**.
- Manages three configurable endpoints:
  - `OPENAI_API_KEY` — OpenAI API Key
  - `NOUS_API_KEY` — Nous API Key
  - `OLLAMA_ENDPOINT` — Ollama Endpoint
- Each field supports:
  - masked/unmasked input toggle via `Eye` / `EyeOff`
  - per-field connection testing
  - status states: `idle`, `testing`, `success`, `error`
- Test behavior is simulated:
  - sets status to `testing`
  - waits 1.5s
  - marks success if the field has a non-empty value, otherwise error
  - resets status to `idle` after 3s
- Uses motion transitions for card entrance, field entrance, and button state changes.

### ClickSpark
See **`clickspark.md`** for the full implementation of `components/bits/ClickSpark.tsx`.

- Implements a reusable click-effect wrapper that draws animated spark particles on a canvas overlay.
- Props include:
  - `sparkColor`
  - `sparkSize`
  - `sparkRadius`
  - `sparkCount`
  - `duration`
  - `className`
- Core behavior:
  - uses a `canvas` positioned absolutely over children
  - resizes to the parent via `ResizeObserver`
  - tracks sparks in a ref and animates them with `requestAnimationFrame`
  - spawns sparks around the click point in evenly spaced directions
- Intended as a generic interaction effect component for wrapping arbitrary child content.

### Sidebar Navigation Component
See **`sidebar_navigation_component.md`** for the full implementation of `src/components/Sidebar.tsx`.

- Provides a collapsible left sidebar for the **Hermes Evolution Dashboard**.
- Navigation pages are defined by the `Page` union:
  - `overview`
  - `skills`
  - `evolution`
  - `datasets`
  - `metrics`
  - `logs`
  - `settings`
- Nav items are icon-labeled buttons with active-state styling and animated label visibility when collapsed/expanded.
- Sidebar sections:
  - logo/header with Hermes branding
  - main navigation list
  - bottom collapse toggle
- Uses dark/light theme-aware colors and animated width changes:
  - expanded width: `240`
  - collapsed width: `64`
- The sidebar is sticky, full height, and designed for the dashboard’s primary navigation structure.