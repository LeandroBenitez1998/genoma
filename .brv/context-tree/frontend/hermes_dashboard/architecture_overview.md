---
title: Architecture Overview
summary: Next.js 16 + FastAPI dashboard with Three.js replaced by CSS gradients, lazy-loaded backend, standalone next.config
tags: []
related: [frontend/hermes_dashboard/hermes_dashboard_frontend.md, frontend/hermes_dashboard/layout.md, frontend/hermes_dashboard/page.md, frontend/hermes_dashboard/globals.md, frontend/hermes_dashboard/route.md]
keywords: []
createdAt: '2026-04-28T02:21:54.807Z'
updatedAt: '2026-04-28T02:21:54.807Z'
---
## Reason
Document Hermes Dashboard architecture from inline context

## Raw Concept
**Task:**
Document Hermes Dashboard architecture

**Changes:**
- Replaced Three.js with CSS gradients
- Backend lazy-loaded
- next.config set to standalone

**Files:**
- src/app/page.tsx
- src/app/layout.tsx
- backend/main.py
- next.config.ts

**Flow:**
Next.js frontend (port 3000) -> FastAPI backend (port 8000)

**Timestamp:** 2026-04-28

## Narrative
### Structure
Next.js 16 frontend with FastAPI backend. Dashboard pages: Overview, Skill Hub, Evolution, Datasets, Memory, Metrics, Logs, Settings.

### Dependencies
Backend requires FastAPI, frontend requires Next.js 16

### Highlights
Performance optimization: Three.js removed, CSS gradients used instead. Backend lazy-loaded for faster initial load.
