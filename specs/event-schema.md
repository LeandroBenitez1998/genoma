# Canonical Run Event Schema v0.1

## Purpose

Define a vendor-neutral event format for agent execution telemetry. Any agent (Hermes, Claude Code, Codex, OpenCode) can emit runs in this schema. The schema is the single source of truth for cross-agent comparison, evaluation, and regression detection.

---

## Design Principles

1. **Agent-agnostic:** No special cases for any single agent. Required fields are minimal; optional fields capture agent-specific context.
2. **Append-only:** New fields may be added to optional sections. Removing or renaming required fields is breaking.
3. **Graceful degradation:** Missing optional fields never break ingestion. Unknown fields go into `context{}` dict.
4. **Deterministic evaluation:** The same run, evaluated twice, always produces identical scores.
5. **Cross-comparable:** Two runs from different agents can be compared on: outcome, token usage, tool calls, errors, improvement delta.

---

## Root Object: `CanonicalRun`

### Required Fields

These fields MUST be present and non-null for a valid run event. Collectors must fail fast if unable to provide them.

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `run_id` | string (UUID) | `"a1b2c3d4-e5f6-..."` | Unique run identifier. Collectors assign via trace_id or session_id. |
| `agent_name` | string | `"hermes"`, `"claude-code"`, `"codex"`, `"opencode"` | Which agent ran this. |
| `collector` | string | `"hermes-trace-ingestor"`, `"claude-code-session-collector"` | Which collector produced this event. Enables audit trail. |
| `started_at` | ISO 8601 string | `"2026-05-19T14:32:00Z"` | When the run began. |
| `task_name` | string | `"Implement user authentication"` | What the agent was asked to do. Max 500 chars; first sentence only. |
| `task_name` | string | (max 500 chars) | Task description (first sentence). |
| `outcome` | enum string | `"success"`, `"failure"`, `"partial"`, `"unknown"` | Did the agent succeed? `success`: no errors, completed. `failure`: critical error. `partial`: partial success with non-critical errors. `unknown`: insufficient info. |

### Optional Fields

These fields MAY be absent or null. Collectors should populate them when available. Evaluators must handle missing values gracefully.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `agent_version` | string | null | Agent version at run time. E.g., `"2.1.143"`. |
| `provider` | string | null | AI provider: `"anthropic"`, `"openai"`, `"hermes"`, `"ollama"`, etc. |
| `model` | string | null | Model ID. E.g., `"claude-opus-4-7"`, `"gpt-4-turbo"`. |
| `repo` | string | null | Source code repo (git remote URL or local path). Used for run grouping. |
| `session_id` | string | null | Unique session UUID from the agent. Links multiple runs to one session. |
| `ended_at` | ISO 8601 string | null | When the run completed. If null, use current time. |
| `tool_calls` | array of objects | `[]` | All tool invocations in sequence. See schema below. |
| `files_touched` | array of objects | `[]` | All files read/written/deleted. See schema below. |
| `artifacts` | array of objects | `[]` | Output artifacts (code, docs, reports). See schema below. |
| `errors` | array of objects | `[]` | Exceptions and error signatures. See schema below. |
| `metrics` | object | null | Aggregated execution metrics. See schema below. |
| `eval_scores` | array of objects | `[]` | Scores from Phase 5 evaluation. Written post-run. See schema below. |
| `improvement_candidates` | array of objects | `[]` | Proposed improvements (Phase 8+). |
| `context` | object | `{}` | Catch-all for agent-specific or collector-specific fields. Never fails ingestion. |
| `resolution` | string | null | How the run was resolved (if outcome == `"failure"`). Diagnostic text. |
| `collector_version` | string | `"0.1.0"` | Version of the collector that produced this event. For forward compatibility. |

---

## Nested Object Schemas

### `ToolCallRecord` (items in `tool_calls[]`)

```json
{
  "id": "tool-call-uuid",
  "name": "Read",
  "input_summary": "Read /path/to/file.ts",
  "duration_ms": 245,
  "result_summary": "Returned 1240 chars",
  "error": null
}
```

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique ID for this tool call. E.g., UUID or sequential counter. |
| `name` | string | Tool name. E.g., `"Read"`, `"Bash"`, `"Edit"`, `"Write"`, `"Grep"`, `"Agent"`. |
| `input_summary` | string | First 200 chars of input. Omit secrets. |
| `duration_ms` | integer | Execution time in milliseconds. Omit if not available. |
| `result_summary` | string | First 200 chars of result/output. |
| `error` | string or null | Error message if tool failed. Otherwise null. |

### `FileTouchRecord` (items in `files_touched[]`)

```json
{
  "path": "src/components/Button.tsx",
  "action": "write",
  "size_bytes": 2048
}
```

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | File path. May be relative or absolute. |
| `action` | string | One of: `"read"`, `"write"`, `"delete"`. |
| `size_bytes` | integer or null | Final file size. Omit for deletes. |

### `RunMetrics` (the `metrics` field)

```json
{
  "input_tokens": 4200,
  "output_tokens": 1850,
  "cache_tokens": 512,
  "latency_ms": 8500,
  "cost_usd": 0.082,
  "tool_call_count": 12
}
```

| Field | Type | Notes |
|-------|------|-------|
| `input_tokens` | integer or null | Tokens sent to model. |
| `output_tokens` | integer or null | Tokens generated by model. |
| `cache_tokens` | integer or null | Cached input tokens (prompt caching). |
| `latency_ms` | integer or null | Total run duration in ms. |
| `cost_usd` | float or null | Estimated cost in USD. |
| `tool_call_count` | integer | Total tool calls made. Defaults to 0. |

### `ErrorRecord` (items in `errors[]`)

```json
{
  "signature": "TypeError: Cannot read property 'foo' of undefined",
  "message": "TypeError: Cannot read property 'foo' of undefined at line 42",
  "stack_excerpt": "at Object.<anonymous> (file.js:42:10)",
  "count": 3
}
```

| Field | Type | Notes |
|-------|------|-------|
| `signature` | string | Error class + first line. Used for deduplication. E.g., `"TypeError: Cannot read property..."`. |
| `message` | string | Full error message. |
| `stack_excerpt` | string | First few stack frames (first 300 chars). |
| `count` | integer | How many times this error occurred. Default 1. |

### `EvalScore` (items in `eval_scores[]`)

Written by Phase 5 evaluation engine. Not set by collectors.

```json
{
  "scorer": "outcome_scorer",
  "score": 1.0,
  "passed": true,
  "details": {
    "outcome": "success",
    "reason": "Run completed without errors"
  }
}
```

| Field | Type | Notes |
|-------|------|-------|
| `scorer` | string | Name of the scorer that produced this. E.g., `"outcome_scorer"`, `"token_cost_scorer"`. |
| `score` | float | Score in range [0.0, 1.0]. |
| `passed` | boolean | Did this scorer report success? |
| `details` | object | Scorer-specific metadata. Free-form. |

### `Artifact` (items in `artifacts[]`)

```json
{
  "path": "output/evolved_skill.md",
  "type": "markdown",
  "size_bytes": 4096
}
```

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | Path to artifact. |
| `type` | string | MIME-like type. E.g., `"markdown"`, `"json"`, `"python"`, `"typescript"`. |
| `size_bytes` | integer | Size in bytes. |

---

## Backward Compatibility

### Mapping from `TraceRecord` (Hermes legacy)

The existing `TraceRecord` dataclass in `backend/promethean/models.py` maps to `CanonicalRun` as follows:

| TraceRecord | CanonicalRun | Mapping rule |
|-------------|--------------|--------------|
| `trace_id` | `run_id` | Direct copy. |
| `agent` | `agent_name` | Direct copy. |
| `agent_version` | `agent_version` | Direct copy. |
| `timestamp` | `started_at` | Direct copy (ISO 8601). |
| — | `ended_at` | Set to `started_at` if missing. |
| `task` | `task_name` | Direct copy. |
| `outcome` | `outcome` | Direct copy (`"success"`, `"failure"`, `"partial"`). |
| `error_signature` | `errors[0].signature` | Wrap in array. If empty, set `errors = []`. |
| `context` | `context` | Direct copy (dict). |
| `resolution` | `resolution` | Direct copy. |
| — | `collector` | Set to `"hermes-trace-ingestor"` (constant). |
| — | `provider` | Set to `"hermes"` (constant). |

All other `CanonicalRun` fields default to null/empty if not present in `TraceRecord`.

### Unknown Fields

If a collector encounters a field not in this schema:
- If it's non-sensitive: include it in `context{}`
- If it's sensitive (API key, secret): omit it
- Never reject the run due to unknown fields

---

## Version History

### v0.1 (current)
- Initial schema
- Maps `TraceRecord` to `CanonicalRun`
- Defines required fields: `run_id`, `agent_name`, `collector`, `started_at`, `task_name`, `outcome`
- Defines optional fields for tools, files, metrics, errors, and scores

### Future versions
- v0.2: Add `parent_run_id` for nested agent calls
- v0.3: Add `reproducibility_hash` for deterministic replay
