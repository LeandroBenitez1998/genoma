-- Canonical run records — normalized across all agents
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    collector TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    task_name TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK(outcome IN ('success', 'failure', 'partial', 'unknown')),
    provider TEXT,
    model TEXT,
    repo TEXT,
    session_id TEXT,
    agent_version TEXT,
    collector_version TEXT,
    resolution TEXT,
    context_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_runs_agent ON runs(agent_name);
CREATE INDEX IF NOT EXISTS idx_runs_outcome ON runs(outcome);
CREATE INDEX IF NOT EXISTS idx_runs_started ON runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_repo ON runs(repo);
CREATE INDEX IF NOT EXISTS idx_runs_session ON runs(session_id);

-- Tool calls made during run execution
CREATE TABLE IF NOT EXISTS tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    tool_id TEXT,
    name TEXT NOT NULL,
    input_summary TEXT,
    duration_ms INTEGER,
    result_summary TEXT,
    error TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_run ON tool_calls(run_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_name ON tool_calls(name);

-- Files touched during run execution
CREATE TABLE IF NOT EXISTS files_touched (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    action TEXT DEFAULT 'write' CHECK(action IN ('read', 'write', 'delete')),
    size_bytes INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_files_touched_run ON files_touched(run_id);
CREATE INDEX IF NOT EXISTS idx_files_touched_path ON files_touched(path);

-- Token counts and latency metrics
CREATE TABLE IF NOT EXISTS run_metrics (
    run_id TEXT PRIMARY KEY REFERENCES runs(run_id) ON DELETE CASCADE,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cache_tokens INTEGER,
    latency_ms INTEGER,
    cost_usd REAL,
    tool_call_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Errors encountered during run
CREATE TABLE IF NOT EXISTS run_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    signature TEXT,
    message TEXT,
    stack_excerpt TEXT,
    count INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_run_errors_sig ON run_errors(signature);
CREATE INDEX IF NOT EXISTS idx_run_errors_run ON run_errors(run_id);

-- Evaluation scores (populated by Phase 5 evaluation engine)
CREATE TABLE IF NOT EXISTS eval_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    scorer TEXT NOT NULL,
    score REAL,
    passed INTEGER,
    details TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_eval_scores_run ON eval_scores(run_id);
CREATE INDEX IF NOT EXISTS idx_eval_scores_scorer ON eval_scores(scorer);

-- Enable WAL mode for better concurrency
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
