---
children_hash: 515c06ea24aed64bdce7f7f3687b2a2d29249f0c442224ad38bee6fc316193d0
compression_ratio: 0.11090342679127727
condensation_order: 0
covers: [api_client_library.md]
covers_token_total: 3210
summary_level: d0
token_count: 356
type: summary
---
# API Client Library

TypeScript API client (`src/lib/api.ts`) providing typed endpoints for jobs, skills, evolution, and WebSocket streaming. React Query-compatible design with resilient infrastructure.

## Architecture

**Resilience Features:**
- AbortController timeouts (default 15s)
- Typed `ApiError` with `ErrorKind`: `network | timeout | server | client`
- Auto-refresh token on 401, retry once
- WebSocket auto-reconnect after 3s

**Auth:** Session token via `X-Hermes-Session-Token` header, lazy-loaded from `/`

**Env:** `NEXT_PUBLIC_API_BASE` → fallback `http://127.0.0.1:9119`

## Key Interfaces

- `SkillInfo`, `SkillDetail` — skill metadata and content
- `EvolutionJob`, `EvolutionRun` — job lifecycle and results
- `MetricsData`, `DatasetInfo`, `ConstraintResult` — analysis data
- `ProviderSummary` — skill provider groupings

## Typed API Functions

**Skills:** `fetchSkills`, `fetchSkill`, `fetchSkillHistory`, `fetchSkillProviders`, `toggleSkillEnabled`, `deleteProviderSkill`, `deleteGlobalSkill`, `refreshSkills`

**Evolution:** `fetchEvolutionRuns`, `fetchSkillDiff`, `startEvolution`

**Jobs:** `fetchJobs`, `fetchJob`, `fetchJobLogs`, `cancelJob`

**Analysis:** `fetchMetrics`, `fetchDatasets`, `fetchDataset`, `validateSkill`

**Infrastructure:** `fetchHealth`, `checkHealth`

---

See **api_client_library.md** for full source with session token logic, WebSocket helper, and typed fetch wrapper.