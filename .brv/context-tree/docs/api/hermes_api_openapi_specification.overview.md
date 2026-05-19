## Hermes API OpenAPI Specification Overview

### Key Points

- **OpenAPI 3.1.0** specification for Hermes backend (FastAPI/Python)
- Base server: `http://127.0.0.1:8000` (overridable via `NEXT_PUBLIC_API_BASE` environment variable)
- Frontend (Next.js) consumes these endpoints with a defined response contract
- **Evolution system** enables iterative skill improvement with scoring (baseline vs evolved scores)
- **Jobs system** provides real-time tracking of evolution runs with status, logs, and progress
- Standardized **ApiError schema** with typed error kinds for consistent frontend error handling
- WebSocket endpoint (`/ws`) noted but streaming details not included in this spec excerpt

---

### Section Structure

| Section | Path Prefix | Methods |
|---|---|---|
| Skills | `/api/skills` | GET (list, detail, evolution-history) |
| Evolution | `/api/evolution` | GET (runs), POST (start) |
| Jobs | `/api/jobs` | GET (list, detail), DELETE (cancel), GET logs |
| Health | `/api/health` | GET |

---

### Notable Schemas

| Schema | Purpose |
|---|---|
| `SkillInfo` | Basic skill metadata (name, path, providers, category, size) |
| `SkillDetail` | Full skill content including parsed frontmatter, body, and raw content |
| `EvolutionRun` | Historical record with baseline_score, evolved_score, improvement |
| `EvolutionJob` | Active job with status enum and progress tracking |
| `ApiError` | Typed error contract (network/timeout/server/client) |

---

### Notable Decisions / Patterns

- **Job status enum** includes 11 states: `queued → loading_skill → building_dataset → validating → configuring → optimizing → evaluating → saving → completed/failed`
- **Evolution constraints**: `iterations` (1-20, default 3), `eval_source` (default: "synthetic")
- **503 handling**: All endpoints share a standardized `ServiceUnavailable` response; frontend shows "Desconectado" state with retry option
- **Health endpoint** exposes system state including `hermes_repo_exists`, `skills_count`, and `categories` breakdown
- **Job logs**: Streaming paginated logs via `?since=` query parameter