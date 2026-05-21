---
confidence: 0.95
sources: [frontend/_index.md, docs/_index.md, backend/_index.md, backend/_index.md]
synthesized_at: '2026-05-21T07:43:50.192Z'
type: synthesis
title: Evolution workflow is end-to-end across UI, API, and job tracking
summary: Evolution runs are started in the UI, tracked by the API contract, and parsed by backend job tracking for live progress and completion states.
tags: [evolution, jobs, frontend, backend, api]
related: []
keywords: [run tracking, job status, polling, diff view, metrics, logs, evolution start, lifecycle]
createdAt: '2026-05-21T07:43:50.192Z'
updatedAt: '2026-05-21T07:43:50.192Z'
---

# Evolution workflow is end-to-end across UI, API, and job tracking

A single evolution workflow spans the dashboard, API surface, and backend orchestration: the frontend starts runs and polls status, the API exposes run/job endpoints, and `JobTracker` parses streamed logs into persistent lifecycle states.

## Evidence

- **frontend**: The Evolution Hub loads evolvable skills, starts jobs with `startEvolution(skillName, 3)`, polls every 2 seconds until completion/failure, and shows run history, diffs, and job badges.
- **docs**: The canonical API includes `/api/evolution/runs`, `/api/evolution/start`, `/api/jobs`, `/api/jobs/{jobId}`, and `/api/jobs/{jobId}/logs`.
- **backend**: `job_tracker.md` defines `JobStatus` with 10 states from `QUEUED` to `COMPLETED`/`FAILED`, and `JobTracker` parses streaming log output using phase, score, and iteration patterns.
- **backend**: `main.py` includes evolution endpoints for start run, list runs, history, diff, metrics, and job endpoints for list, get, logs, and cancel.
