## API Client Library Overview

**File:** `src/lib/api.ts`
**Type:** TypeScript API client with typed endpoints and WebSocket support
**Purpose:** Frontend API client for Hermes backend (skills, evolution, jobs, WebSocket)

---

### Key Points

- **Typed API client** using a central `api<T>()` wrapper with AbortController timeouts (default 15s)
- **Hermes session authentication** via `X-Hermes-Session-Token` header with automatic token refresh on 401
- **Environment resolution:** Supports `NEXT_PUBLIC_API_BASE` and legacy `NEXT_PUBLIC_API_URL`; falls back to `http://127.0.0.1:9119`
- **Typed errors** via `ApiError` class with `ErrorKind`: `network`, `timeout`, `server`, `client`
- **WebSocket helper** (`wsConnect`) with auto-reconnect after 3s and JSON message parsing
- **Health check endpoint** uses `/api/status` (no auth required) for circuit breaker connectivity checks
- **Comprehensive typed interfaces** for skills, evolution runs, jobs, datasets, and constraints

---

### Structure / Sections Summary

1. **Infrastructure Setup**
   - Base URL resolution with fallback to `127.0.0.1:9119`
   - Session token fetching from HTML `__HERMES_SESSION_TOKEN__`

2. **Error Handling**
   - `ApiError` class with status, kind, endpoint tracking
   - `isApiError` type guard

3. **Core Fetch Wrapper**
   - `executeRequest<T>()` — low-level fetch with AbortController
   - `api<T>()` — high-level wrapper with token injection and 401 retry logic

4. **WebSocket Helper**
   - `wsConnect(onMessage)` — lazy token, query param auth, auto-reconnect

5. **Health Check**
   - `checkHealth()` — returns `{ok, kind?, message?}`

6. **Typed API Endpoints**
   - Skills: `fetchSkills`, `fetchSkill`, `fetchSkillHistory`, `fetchSkillProviders`, `toggleSkillEnabled`, `deleteProviderSkill`, `deleteGlobalSkill`, `refreshSkills`
   - Evolution: `fetchEvolutionRuns`, `fetchSkillDiff`, `startEvolution`
   - Jobs: `fetchJobs`, `fetchJob`, `fetchJobLogs`, `cancelJob`
   - Metrics/Datasets: `fetchMetrics`, `fetchDatasets`, `fetchDataset`
   - Constraints: `validateSkill`
   - Health: `fetchHealth`

---

### Notable Interfaces

| Interface | Fields |
|-----------|--------|
| `SkillInfo` | name, path, description, size, providers, category |
| `EvolutionRun` | skill_name, baseline_score, evolved_score, improvement, iterations |
| `EvolutionJob` | id, status, current_iteration, pid, progress, logs |
| `MetricsData` | total_runs, avg_improvement, success_rate, runs |
| `ConstraintResult` | passed, constraint, message, details |
| `ApiError` | kind (ErrorKind), status, endpoint |

---

### Notable Patterns

- **Token caching** via `_sessionToken` / `_tokenPromise` with lazy initialization
- **AbortController** for request timeout with `setTimeout` + `controller.abort()`
- **WebSocket auto-reconnect** on `onclose` event (3s delay)
- **URL encoding** via `encodeURIComponent` for skill names in paths