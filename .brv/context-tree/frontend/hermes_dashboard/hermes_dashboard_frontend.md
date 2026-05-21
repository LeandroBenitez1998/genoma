---
title: Hermes Dashboard Frontend
summary: Next.js frontend provides dashboard pages for overview, evolution, skills, curator, datasets, logs, metrics, and settings.
tags: []
related: [frontend/hermes_dashboard/architecture_overview.md, frontend/hermes_dashboard/layout.md, frontend/hermes_dashboard/page.md, frontend/hermes_dashboard/globals.md, frontend/hermes_dashboard/route.md]
keywords: []
createdAt: '2026-05-21T07:40:35.542Z'
updatedAt: '2026-05-21T07:40:35.542Z'
---
## Reason
Curate frontend app structure and pages

## Raw Concept
**Task:**
Document dashboard frontend structure and pages

**Files:**
- src/app/page.tsx
- src/app/layout.tsx
- src/app/evolution/page.tsx
- src/app/skills/page.tsx

**Flow:**
route -> layout -> page components -> UI primitives

**Timestamp:** 2026-05-21

## Narrative
### Structure
Frontend uses app router pages with shared components, UI primitives, query provider, and themed backgrounds.

### Highlights
Dashboard pages expose curator, skill studio, logs, metrics, settings, and evolution views.
