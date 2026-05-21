---
children_hash: 1b7d29a62cab14bf9961854c163c6d4a3147369b63e9fa513cb3e3f5fe48cc06
compression_ratio: 0.5912679981421273
condensation_order: 2
covers: [backend/_index.md, collectors/_index.md, eval/_index.md, evolution-workflow-is-end-to-end-across-ui-api-and-job-tracking.md, promethean/_index.md, storage/_index.md]
covers_token_total: 2153
summary_level: d2
token_count: 1273
type: summary
---
# Backend Knowledge Summary

## Package-level structure
The backend knowledge cluster covers the FastAPI application, ingestion collectors, evaluation pipeline, Promethean orchestration, and run storage. The core pattern across these areas is a shared flow from **source → analysis → curated knowledge**, with `CanonicalRun` and run/job metadata acting as the connective tissue between ingestion, tracking, and downstream use.

## Main backend application
### **backend/_index.md**
- The backend domain is the `hermes-dashboard` FastAPI backend that bridges the Next.js frontend to the `hermes-agent-self-evolution` system.
- Key modules:
  - **`init.md`** — empty Python module placeholder.
  - **`job_tracker.md`** — persistent job tracking for evolution runs.
  - **`main.md`** — FastAPI app with ~20 REST endpoints plus a WebSocket.
  - **`requirements.md`** — core dependencies (`fastapi`, `uvicorn[standard]`, `websockets`, `pyyaml`).
- Important relationships:
  - `main.py` imports and uses `job_tracker` singleton types like `JobStatus` and `EvolutionJob`.
  - Both `main.py` and `job_tracker.py` reference `HERMES_AGENT_REPO` and `EVOLUTION_DIR`.
  - Job tracking supports real-time progress parsing for evolution streaming over WebSocket.

### **job_tracker.md**
- Defines the lifecycle for evolution jobs using a `JobStatus` enum with 10 states from `QUEUED` through `COMPLETED`/`FAILED`.
- `EvolutionJob` stores `skill_name`, `iterations`, `progress`, `scores`, and logs.
- `JobTracker` parses streaming logs using regex patterns such as `PHASE_PATTERNS`, `SCORE_PATTERN`, and `ITER_PATTERN`.
- Logs are persisted to `~/.hermes/evolution-logs/`.

### **main.md**
- Provides the primary FastAPI surface for the system.
- Exposes skill endpoints, evolution endpoints, job endpoints, dataset endpoints, graph generation, and metrics/constraint validation.
- The graph endpoint emits `vis.js` format from skills, memory, and evolution runs, including community detection.
- Uses Ollama when available and falls back to cloud providers.

### **requirements.md**
- Declares backend runtime dependencies, anchored around FastAPI, Uvicorn, WebSockets, and PyYAML.

## Ingestion and normalization
### **collectors/_index.md**
- The collectors package normalizes session and trace data into the shared `CanonicalRun` schema.
- It is the source layer for run normalization before analysis and storage.
- The two primary adapters are:
  - **Claude Code Collector**
  - **Hermes Collector**

### **Claude Code Collector**
- Converts Claude Code session JSONL logs into `CanonicalRun` objects.
- Default source root is `~/.claude/projects`.
- Extracts:
  - `run_id`, `task_name`, `started_at`, `ended_at`, `model`, `repo`
  - `tool_calls`, `metrics`, `errors`, `context.cwd`
- `collect_all(project_path=None, limit=50)` recursively scans `.jsonl` files and skips malformed sessions.
- Outcome inference is heuristic:
  - system errors → `partial` or `failure`
  - assistant `stop_reason == "end_turn"` → `success`
  - otherwise `unknown`

### **Hermes Collector**
- Wraps `TraceIngestor` and converts `TraceRecord` data into `CanonicalRun`.
- Focuses on schema normalization rather than raw log parsing.
- Supports:
  - `collect_from_trace(trace)` → `trace.to_canonical()`
  - `collect_batch(traces)`
  - `load_from_disk(limit=100)`
  - `get_run_by_id(run_id)`
- Skips malformed trace files during disk loading.

### Ingestion relationship
- Both collectors produce `CanonicalRun` as the common contract.
- Claude Code Collector handles raw session parsing.
- Hermes Collector handles already-ingested trace normalization.
- Together they provide backend entry points for normalized run capture.

## Evaluation
### **eval/_index.md**
- The evaluation engine is the backend scoring pipeline for traces and generated dataset evaluation.
- Core file: `backend/eval/engine.py`.
- The summary indicates the same source → analysis → curated knowledge flow, but details are concentrated in `evaluation_engine.md`.

## Promethean orchestration
### **promethean/_index.md**
- Scope: `backend/promethean/cycle_orchestrator.py`.
- Core role: coordinates iterative evolution and skill deployment.
- Uses the same source → analysis → curated knowledge workflow.
- This area represents the cycle-driven orchestration layer above the backend runtime and deployment flow.

## Storage
### **storage/_index.md**
- Storage documents the execution persistence layer and metadata management.
- Primary implementation file: `backend/storage/run_store.py`.
- Emphasizes SQL schema plus run storage helpers.
- Main purpose: persist execution metadata and support run tracking.

## Cross-cutting relationships
- **UI → API → job tracking** forms a single end-to-end evolution workflow.
- **Collectors** normalize raw inputs into `CanonicalRun`.
- **JobTracker** turns streamed evolution output into persistent lifecycle states.
- **Run store** persists execution metadata for later retrieval and analysis.
- **Promethean orchestration** coordinates iterative evolution and deployment using the same structured pipeline.