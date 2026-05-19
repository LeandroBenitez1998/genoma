# Architecture Overview: Hermes Dashboard

## Key Points

- **Tech Stack**: Next.js 16 frontend with FastAPI backend
- **Performance Optimization**: Three.js removed; CSS gradients now used for visual effects
- **Backend Strategy**: Lazy-loaded backend for faster initial page load
- **Deployment Config**: `next.config.ts` set to `standalone` mode
- **Communication Flow**: Frontend (port 3000) ↔ Backend (port 8000)

## Structure / Sections Summary

### Raw Concept
- Task: Document Hermes Dashboard architecture
- Key changes: Three.js removal, CSS gradients, lazy backend, standalone config
- Target files: `src/app/page.tsx`, `src/app/layout.tsx`, `backend/main.py`, `next.config.ts`

### Narrative
- **Structure**: Next.js 16 frontend + FastAPI backend with 8 dashboard pages (Overview, Skill Hub, Evolution, Datasets, Memory, Metrics, Logs, Settings)
- **Dependencies**: FastAPI (backend), Next.js 16 (frontend)

## Notable Entities & Decisions

| Entity | Details |
|--------|---------|
| **Frontend** | Next.js 16, port 3000 |
| **Backend** | FastAPI, port 8000, lazy-loaded |
| **Build Config** | `standalone` mode enabled |
| **Visual System** | CSS gradients (replaced Three.js) |

### Decisions
- **Three.js removal**: Reduces bundle size; CSS gradients sufficient for dashboard visuals
- **Lazy backend loading**: Improves initial load time; backend services load on demand
- **Standalone next.config**: Self-contained Next.js output for simplified deployment