---
children_hash: e33790775d9f0bf0075f37cfb501e631426ba5982fcaa06738a6e852fe8a68f3
compression_ratio: 0.1744998794890335
condensation_order: 1
covers: [claude_code_collector.md, collectors.md, hermes_collector.md]
covers_token_total: 4149
summary_level: d1
token_count: 724
type: summary
---
## Collectors

The `backend/collectors` package provides ingestion adapters that normalize session/trace data into the shared `CanonicalRun` schema. The package is centered on two collectors: **Claude Code Collector** and **Hermes Collector**, both operating as backend bridges from raw runtime records to curated run metadata.

### Package role
- Owns collector implementations for session and trace ingestion.
- Acts as the source layer for run normalization before downstream analysis and storage.
- See **Collectors** for the package-level purpose and **Claude Code Collector** / **Hermes Collector** for implementation details.

### Claude Code Collector
- `Claude Code Collector` converts Claude Code session JSONL logs into `CanonicalRun` objects.
- Uses `CLAUDE_SESSIONS_DIR = Path.home() / ".claude" / "projects"` as the default search root.
- Key fields extracted per run:
  - `run_id` from attachment or message `sessionId`
  - `task_name` from first user text content
  - `started_at` / `ended_at` from event timestamps
  - `model` from assistant messages
  - `repo` from attachment `gitBranch`
  - `tool_calls` from assistant `tool_use` items
  - `metrics` from assistant token usage
  - `errors` from system events
  - `context.cwd` from attachment `cwd`
- `collect_all(project_path=None, limit=50)` scans `.jsonl` files recursively and skips malformed sessions.
- Outcome inference is heuristic:
  - system errors → `partial` or `failure`
  - assistant `stop_reason == "end_turn"` → `success`
  - otherwise `unknown`
- File reference for drill-down: **Claude Code Collector**

### Hermes Collector
- `Hermes Collector` wraps `TraceIngestor` and converts `TraceRecord` data into `CanonicalRun`.
- Primary responsibility is schema normalization rather than parsing raw logs.
- Key operations:
  - `collect_from_trace(trace)` → `trace.to_canonical()`
  - `collect_batch(traces)` → batch conversion
  - `load_from_disk(limit=100)` → reads ingested `.json` traces from `INGESTED_DIR`
  - `get_run_by_id(run_id)` → searches trace files containing the run ID and returns the matching canonical run
- Resilient to malformed trace files by skipping failures during disk load.
- File reference for drill-down: **Hermes Collector**

### Relationship to ingestion pipeline
- Both collectors produce `CanonicalRun` as the common contract.
- `Claude Code Collector` handles raw session log parsing and event extraction.
- `Hermes Collector` handles already-ingested traces through `TraceIngestor` and `TraceRecord`.
- Together they provide the backend entry points for normalized run capture across Claude Code sessions and Hermes traces.

### Drill-down map
- **Collectors** — package overview and ingestion responsibilities
- **Claude Code Collector** — JSONL session parsing, field extraction, outcome inference
- **Hermes Collector** — trace-to-canonical conversion, disk loading, run lookup