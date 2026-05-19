# Agent-Agnostic Agent Intelligence Platform Plan

> **For Hermes:** Use `subagent-driven-development` only after the spec is approved. This plan is deliberately agent-agnostic so Claude Code, OpenCode, Codex, Hermes, and future agents can all emit comparable telemetry.

**Goal:** Build a vendor-neutral platform that works with *any* agent, ingests their runs through explicit collectors, normalizes execution traces, evaluates outcomes, and surfaces measurable improvements through a dashboard.

**Architecture:** The system is split into four layers: (1) collectors / adapters that ingest each agent’s native CLI or log output into a shared event schema, (2) a normalization and storage layer, (3) an evaluation engine that runs tests/scoring/benchmarks, and (4) a dashboard/API layer that reads the stored data and visualizes runs, comparisons, regressions, and suggested improvements. The dashboard does not capture runs; it is a consumer of the platform’s data.

**Tech Stack:** Shared event schema in JSONL or SQLite/Postgres, CLI collectors and adapter modules per agent, evaluation workers, web dashboard, optional MCP server for agent access, and export/import hooks for CI and PR workflows.

---

## Problem Statement

Today, agent improvements are usually trapped inside a single ecosystem. That creates three problems:

1. The data model is proprietary to one agent.
2. Evaluation results are not comparable across tools.
3. Improvement loops cannot be reused by different agents.

The product should solve the opposite problem: *one canonical telemetry and improvement layer* that any agent can plug into.

---

## Non-Goals

- Rebuilding Claude Code, OpenCode, Codex, or Hermes internally.
- Forcing all agents to use the same runtime or CLI.
- Optimizing for pretty charts before having trustworthy data.
- Automating code changes without review or rollback.

---

## Product Shape

The system should answer these questions:

- What did the agent try to do?
- Which tools did it call?
- What files or artifacts changed?
- Where did it fail?
- Did the change improve the target metric?
- How does one agent compare with another on the same task?

If it cannot answer those questions, it is not yet the product.

---

## Core Concepts

### 1) Collector / Ingestor
A small module or wrapper that captures a native agent run from CLI output, logs, JSON, or session files and converts it into the canonical schema.

Examples:
- Hermes CLI collector
- Claude Code collector
- Codex collector
- OpenCode collector

The collector is the only layer that knows how a specific agent speaks. Everything after this point should be agent-neutral.

### 2) Canonical Run Event Schema
Minimum fields:

- `run_id`
- `agent_name`
- `provider`
- `model`
- `repo`
- `session_id`
- `task_name`
- `started_at`
- `ended_at`
- `tool_calls[]`
- `files_touched[]`
- `artifacts[]`
- `errors[]`
- `metrics{}`
- `eval_scores[]`
- `improvement_candidates[]`

### 3) Normalization + Storage Layer
Takes collector output, deduplicates it, stores it, and makes it queryable.

This layer owns:
- schema validation
- event normalization
- persistence
- indexing

### 4) Evaluation Engine
Runs deterministic checks over a run:

- unit tests
- lint/type checks
- benchmark tasks
- regression detection
- semantic scoring
- cost and latency scoring

### 5) Dashboard
Shows:

- per-run timelines
- agent comparisons
- regressions
- best-performing variants
- suggested prompt/skill/tool-description changes

The dashboard is read-only with respect to ingestion. It visualizes the state created by collectors, storage, and evaluation.

### 6) Optional Improvement Loop
Generates candidate improvements for:

- prompts
- skills
- tool descriptions
- code paths

But those changes should be gated by tests and human review.


---

## Architecture Decision

### Chosen path: Event-first, UI-second

Do **not** start with the dashboard UI.
Start with the event contract and adapters.

Why:
- if the schema is wrong, the UI becomes a lie
- if the adapters are weak, the data is noisy
- if the evaluator is unclear, the charts are decorative only

---

## MVP Scope

The MVP should include:

1. One shared event schema
2. Two collectors at minimum
   - Hermes
   - Claude Code or Codex
3. A storage backend
4. A basic evaluator
5. A dashboard with:
   - list of runs
   - run detail view
   - agent comparison view
   - score trend view
6. Export to JSON/CSV

---

## Phase 1: Define the Canonical Schema

**Objective:** Establish the minimum event format that every agent can emit.

**Files:**
- Create: `specs/event-schema.md`
- Create: `specs/examples/run.jsonl`
- Create: `src/schema/README.md` if code exists later

**Deliverable:**
A written contract for runs, tools, artifacts, errors, and evaluation metrics.

**Verification:**
- Schema covers Hermes, Claude Code, Codex, and OpenCode without special casing.
- Example payloads are valid JSON.

---

## Phase 2: Build the Hermes Collector

**Objective:** Convert Hermes CLI output, session logs, or JSON traces into the canonical schema.

**Files:**
- Create: `src/collectors/hermes_collector.py`
- Create: `tests/collectors/test_hermes_collector.py`

**What it must extract:**
- session metadata
- tool calls
- final output
- errors
- touched files when available

**Verification:**
- A sample Hermes run converts into a valid canonical event.
- Missing optional fields do not break the collector.

---

## Phase 3: Build One Non-Hermes Collector

**Objective:** Prove the system is not Hermes-specific.

**Files:**
- Create: `src/collectors/claude_code_collector.py` or `src/collectors/codex_collector.py`
- Create: `tests/collectors/test_non_hermes_collector.py`

**Verification:**
- The output structure matches the Hermes collector output shape.
- A comparison test confirms parity of required fields.

---

## Phase 4: Add Storage and Query Layer

**Objective:** Persist runs and make them queryable.

**Files:**
- Create: `src/storage/*.py`
- Create: `tests/storage/*.py`

**Storage choice:**
- SQLite for MVP
- Postgres if multi-user and remote access are needed early

**Verification:**
- Insert run
- Query by agent
- Query by repo
- Query by date
- Query by score

---

## Phase 5: Implement the Evaluation Engine

**Objective:** Score runs consistently across agents.

**Files:**
- Create: `src/eval/engine.py`
- Create: `tests/eval/test_engine.py`

**Metrics to start with:**
- tests pass/fail
- diff size
- number of tool calls
- latency
- token/cost estimate
- task success

**Verification:**
- The same run always scores the same way.
- A failing benchmark produces an explicit regression entry.

---

## Phase 6: Build the Dashboard API

**Objective:** Expose runs, metrics, and comparisons to the UI.

**Files:**
- Create: `src/api/*.py`
- Create: `tests/api/*.py`

**Endpoints to include:**
- `GET /runs`
- `GET /runs/:id`
- `GET /agents`
- `GET /comparisons`
- `GET /metrics/trends`

**Verification:**
- API returns canonical event data without agent-specific branching.

---

## Phase 7: Build the Dashboard UI

**Objective:** Make the data readable and actionable.

**Files:**
- Create: `web/*`

**Views:**
- Run list
- Run detail
- Agent comparison
- Regression timeline
- Improvement suggestions

**Verification:**
- A user can inspect a run in under 30 seconds.
- A user can compare two agents on the same task.

---

## Phase 8: Add the Improvement Loop

**Objective:** Turn observations into candidate improvements.

**Files:**
- Create: `src/improve/*.py`
- Create: `tests/improve/*.py`

**Allowed improvements:**
- prompt edits
- skill edits
- tool description edits
- code patches behind review gates

**Guardrails:**
- never auto-merge to main
- never change semantics without a regression gate
- never bypass tests

**Verification:**
- Candidate improvements are stored as proposals, not applied directly.

---

## Phase 9: Add Agent-Readable Access

**Objective:** Let agents query the system themselves.

**Files:**
- Create: `src/mcp/server.py` if using MCP
- Create: `tests/mcp/test_server.py`

**Useful tools for agents:**
- get recent runs
- fetch latest regression
- fetch best-known variant
- compare two runs
- read score trend

**Verification:**
- At least one agent can consume the system programmatically.

---

## Risk Register

### Risk 1: Inconsistent source formats
Different agents expose wildly different logs.

**Mitigation:** adapters must normalize into the same schema and drop unsupported noise.

### Risk 2: False confidence from weak evaluation
Pretty UI can hide bad metrics.

**Mitigation:** tests and benchmark gates must be first-class, not optional.

### Risk 3: Overfitting to one agent
The system accidentally becomes “Hermes with some plugins”.

**Mitigation:** require at least one non-Hermes adapter before declaring MVP complete.

### Risk 4: Improvement automation becomes unsafe
Auto-generated changes can regress silently.

**Mitigation:** every proposed change requires human approval plus an eval gate.

---

## MVP Success Criteria

The MVP is good enough if it can:

- ingest at least two agent types
- normalize them into one schema
- score runs consistently
- compare runs side by side
- surface regressions clearly
- export data for downstream analysis

If it cannot do that, it is still a demo.

---

## Recommended Build Order

1. Canonical schema
2. Hermes adapter
3. One other agent adapter
4. Storage layer
5. Evaluation engine
6. Dashboard API
7. UI
8. Improvement loop
9. MCP access

This order is intentional. Skip it and you get a prettier version of the same ambiguity.

---

## Open Questions

- Should storage be SQLite first or Postgres from day one?
- Should the adapters read raw CLI output, session files, or both?
- Should the dashboard be local-first or multi-user from the start?
- Which metric matters most for the first release: correctness, speed, or cost?

---

## Final Note

This should be treated as infrastructure, not as a single-agent feature.
If Hermes is the only system that fits, the design is wrong.
