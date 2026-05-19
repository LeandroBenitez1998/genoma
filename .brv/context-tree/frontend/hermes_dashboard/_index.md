---
children_hash: 05120e17ddf4ed76482037a8b67a15c5e41ea8a011162c03430a7d52723952f2
compression_ratio: 0.6966292134831461
condensation_order: 1
covers: [architecture_overview.md]
covers_token_total: 267
summary_level: d1
token_count: 186
type: summary
---
# Hermes Dashboard Architecture

## Overview
Next.js 16 frontend paired with FastAPI backend, communicating across ports 3000 and 8000 respectively.

## Frontend Stack
- **Framework:** Next.js 16
- **UI Optimization:** Three.js removed → CSS gradients for lighter footprint
- **Config:** `next.config.ts` set to standalone mode
- **Key Files:** `src/app/page.tsx`, `src/app/layout.tsx`

## Dashboard Pages
Overview · Skill Hub · Evolution · Datasets · Memory · Metrics · Logs · Settings

## Backend
- **Framework:** FastAPI
- **Lazy-loaded:** Backend components loaded on-demand for faster initial frontend load
- **Key File:** `backend/main.py`

## Performance Decision
CSS gradients replace Three.js → reduced bundle size, faster rendering.