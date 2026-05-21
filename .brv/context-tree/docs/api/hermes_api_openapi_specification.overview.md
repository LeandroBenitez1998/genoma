- OpenAPI 3.1 specification for the Hermes Agent API used by the Next.js dashboard and the hermes-cli/FastAPI backend gateway.
- Defines major endpoint groups for skills, evolution runs, jobs, and backend health checks.
- Standardizes typed JSON responses via reusable schemas such as SkillInfo, SkillDetail, EvolutionRun, EvolutionJob, ApiError, and HealthStatus.
- Establishes a unified error-handling contract: any non-2xx or network failure maps to ApiError, and 503 responses indicate a disconnected state in the frontend.
- Includes evolution lifecycle operations, job management actions, paginated job logs, and a health endpoint that reports repository and skill/evolution directory status.
- Notes configuration behavior: NEXT_PUBLIC_API_BASE can override the default local server URL.
- Documents validation/pattern expectations for endpoint paths and enumerates EvolutionJob status values.
Structure / sections summary:
- Top-level metadata and rationale for documenting the backend API contract.
- Narrative section describing the document’s structure, dependencies, highlights, and frontend rules.
- Full OpenAPI definition with server configuration, path operations for /api/skills, /api/evolution, /api/jobs, and /api/health.
- Components section defining schemas for skills, runs, jobs, typed errors, health status, and the standardized ServiceUnavailable response.
Notable entities, patterns, or decisions:
- Endpoint regex patterns are explicitly listed for routing/contract clarity.
- ServiceUnavailable is the standardized 503 fallback used to drive “Desconectado” UI behavior and retry affordances.
- EvolutionJob status enum captures the full job lifecycle from queued through completed/failed.
- The spec distinguishes skill listing/detail/history, evolution start/runs, job retrieval/cancel/logs, and health reporting as separate contract surfaces.