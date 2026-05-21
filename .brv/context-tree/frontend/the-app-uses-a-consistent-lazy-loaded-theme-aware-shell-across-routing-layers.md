---
confidence: 0.89
sources: [frontend/_index.md, frontend/_index.md, frontend/_index.md, src/_index.md]
synthesized_at: '2026-05-21T07:43:50.194Z'
type: synthesis
title: The app uses a consistent lazy-loaded, theme-aware shell across routing layers
summary: Dashboard pages, app shell, and shared UI all follow a lazy-loaded, theme-aware pattern with sidebars, provider wrappers, and animated composition.
tags: [frontend, ui, theme, routing, components]
related: []
keywords: [lazy loading, theme aware, app router, sidebar, providers, framer motion, dashboard shell, navigation]
createdAt: '2026-05-21T07:43:50.194Z'
updatedAt: '2026-05-21T07:43:50.194Z'
---

# The app uses a consistent lazy-loaded, theme-aware shell across routing layers

The frontend is organized around a shared shell and lazy-loaded page composition: the App Router layout provides theme bootstrapping and providers, the page registry loads sections dynamically, and shared UI components support the same interaction model.

## Evidence

- **frontend**: `app/layout.tsx` loads Inter and Geist Mono, wraps the app with TooltipProvider and ReactQueryProvider, renders ThemeAwareBackground, and injects dark-mode bootstrapping from localStorage/system preference.
- **frontend**: The dashboard uses a sticky, collapsible, icon-labeled sidebar, a lazy-loaded page registry, and local state for page selection across overview, skills, evolution, datasets, memory, metrics, logs, and settings.
- **frontend**: The frontend architecture is described as a Next.js 16 App Router dashboard with client-side React, Framer Motion transitions, Tailwind-style utility classes, and lazy-loaded page content.
- **src**: Reusable UI components include shared dashboard building blocks for composition and interaction, including ApiConfigCard, sidebar/navigation, theme controls, and animated UI bits.
