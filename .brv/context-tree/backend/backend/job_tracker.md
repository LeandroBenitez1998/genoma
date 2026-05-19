---
title: job_tracker
summary: ''
tags: []
related: []
keywords: []
createdAt: '2026-04-28T01:33:30.561Z'
updatedAt: '2026-04-28T01:33:30.561Z'
---
## Reason
Preserving complete backend/job_tracker.py from hermes-dashboard project

## Raw Concept
**Task:**
Preserve backend/job_tracker.py

**Files:**
- backend/job_tracker.py

**Timestamp:** 2026-04-28

**Patterns:**
- `class JobStatus` - Python class definition
- `class EvolutionJob` - Python class definition
- `class JobTracker` - Python class definition

## Narrative
### Structure
Python file with 3 classes and 0 functions

### Dependencies
Classes: JobStatus, EvolutionJob, JobTracker

### Highlights
Source: hermes-dashboard/backend/job_tracker.py

---


&quot;&quot;&quot;Evolution job tracking — persistent state for active and completed jobs.&quot;&quot;&quot;

import json
import re
import uuid
import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

LOG_DIR = Path.home() / &quot;.hermes&quot; / &quot;evolution-logs&quot;


class JobStatus(str, Enum):
    QUEUED = &quot;queued&quot;
    LOADING_SKILL = &quot;loading_skill&quot;
    BUILDING_DATASET = &quot;building_dataset&quot;
    VALIDATING = &quot;validating&quot;
    CONFIGURING = &quot;configuring&quot;
    OPTIMIZING = &quot;optimizing&quot;
    EVALUATING = &quot;evaluating&quot;
    SAVING = &quot;saving&quot;
    COMPLETED = &quot;completed&quot;
    FAILED = &quot;failed&quot;


# Phases in order (for progress calculation)
PHASE_ORDER = [
    JobStatus.LOADING_SKILL,
    JobStatus.BUILDING_DATASET,
    JobStatus.VALIDATING,
    JobStatus.CONFIGURING,
    JobStatus.OPTIMIZING,
    JobStatus.EVALUATING,
    JobStatus.SAVING,
]


@dataclass
class EvolutionJob:
    id: str
    skill_name: str
    status: JobStatus = JobStatus.QUEUED
    iterations: int = 3
    current_iteration: int = 0
    pid: Optional[int] = None
    started_at: str = &quot;&quot;
    completed_at: str = &quot;&quot;
    baseline_score: Optional[float] = None
    current_best_score: Optional[float] = None
    evolved_score: Optional[float] = None
    improvement: Optional[float] = None
    error: str = &quot;&quot;
    logs: list[str] = field(default_factory=list)

    def to_dict(self) -&gt; dict:
        d = asdict(self)
        d[&quot;status&quot;] = self.status.value
        return d

    @property
    def progress(self) -&gt; float:
        &quot;&quot;&quot;0.0 to 1.0 progress estimate.&quot;&quot;&quot;
        if self.status == JobStatus.COMPLETED:
            return 1.0
        if self.status == JobStatus.FAILED:
            return 0.0
        if self.status == JobStatus.QUEUED:
            return 0.0

        # Phase-based progress
        phase_idx = 0
        try:
            phase_idx = PHASE_ORDER.index(self.status)
        except ValueError:
            pass

        phase_weight = 1.0 / len(PHASE_ORDER)

        # Within OPTIMIZING phase, use iteration progress
        if self.status == JobStatus.OPTIMIZING and self.iterations &gt; 0:
            iter_progress = self.current_iteration / self.iterations
            base = phase_idx * phase_weight
            return base + (iter_progress * phase_weight)

        return phase_idx * phase_weight

    def add_log(self, message: str):
        timestamp = datetime.now().isoformat()[:19]
        self.logs.append(f&quot;[{timestamp}] {message}&quot;)
        # Keep last 500 lines
        if len(self.logs) &gt; 500:
            self.logs = self.logs[-500:]

    def save_log(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / f&quot;{self.id}.json&quot;
        log_file.write_text(json.dumps(self.to_dict(), indent=2))


class JobTracker:
    def __init__(self):
        self._jobs: dict[str, EvolutionJob] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    def create_job(self, skill_name: str, iterations: int) -&gt; EvolutionJob:
        job_id = f&quot;{skill_name}_{datetime.now().strftime(&apos;%Y%m%d_%H%M%S&apos;)}_{uuid.uuid4().hex[:6]}&quot;
        job = EvolutionJob(
            id=job_id,
            skill_name=skill_name,
            iterations=iterations,
            started_at=datetime.now().isoformat(),
        )
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -&gt; Optional[EvolutionJob]:
        return self._jobs.get(job_id)

    def get_active_jobs(self) -&gt; list[EvolutionJob]:
        return [
            j for j in self._jobs.values()
            if j.status not in (JobStatus.COMPLETED, JobStatus.FAILED)
        ]

    def get_all_jobs(self, limit: int = 50) -&gt; list[EvolutionJob]:
        sorted_jobs = sorted(
            self._jobs.values(),
            key=lambda j: j.started_at,
            reverse=True,
        )
        return sorted_jobs[:limit]

    def set_process(self, job_id: str, process: asyncio.subprocess.Process):
        self._processes[job_id] = process

    def get_process(self, job_id: str) -&gt; Optional[asyncio.subprocess.Process]:
        return self._processes.get(job_id)

    def cleanup_process(self, job_id: str):
        self._processes.pop(job_id, None)

    # ── Log parsing ─────────────────────────────────────────────────

    # Patterns to detect phase changes from Rich output
    PHASE_PATTERNS = [
        (r&quot;Loaded:.*\.md&quot;, JobStatus.LOADING_SKILL),
        (r&quot;Building evaluation dataset&quot;, JobStatus.BUILDING_DATASET),
        (r&quot;Generated.*synthetic examples&quot;, JobStatus.BUILDING_DATASET),
        (r&quot;Mined.*examples from session&quot;, JobStatus.BUILDING_DATASET),
        (r&quot;Loaded golden dataset&quot;, JobStatus.BUILDING_DATASET),
        (r&quot;Validating baseline constraints&quot;, JobStatus.VALIDATING),
        (r&quot;Configuring optimizer&quot;, JobStatus.CONFIGURING),
        (r&quot;Running GEPA optimization&quot;, JobStatus.OPTIMIZING),
        (r&quot;Running MIPROv2&quot;, JobStatus.OPTIMIZING),
        (r&quot;Optimization completed&quot;, JobStatus.OPTIMIZING),
        (r&quot;Validating evolved skill&quot;, JobStatus.EVALUATING),
        (r&quot;Evaluating on holdout&quot;, JobStatus.EVALUATING),
        (r&quot;Evolution Results&quot;, JobStatus.SAVING),
        (r&quot;Saved.*to output&quot;, JobStatus.SAVING),
        (r&quot;✓ Skill evolved&quot;, JobStatus.COMPLETED),
    ]

    # Pattern to extract scores
    SCORE_PATTERN = re.compile(r&quot;baseline[=_:\s]+(\d+\.?\d*)|evolved[=_:\s]+(\d+\.?\d*)|score[=_:\s]+(\d+\.?\d*)|improvement[=_:\s]+([+-]?\d+\.?\d*)&quot;, re.IGNORECASE)

    # Pattern to extract iteration number
    ITER_PATTERN = re.compile(r&quot;iteration[=:\s]+(\d+)|eval[=:\s#]+(\d+)/(\d+)&quot;, re.IGNORECASE)

    def parse_line(self, job: EvolutionJob, line: str):
        &quot;&quot;&quot;Parse a log line and update job state.&quot;&quot;&quot;
        # Strip ANSI codes
        clean = re.sub(r&quot;\x1b\[[0-9;]*m&quot;, &quot;&quot;, line).strip()
        if not clean:
            return

        job.add_log(clean)

        # Check phase transitions
        for pattern, phase in self.PHASE_PATTERNS:
            if re.search(pattern, clean, re.IGNORECASE):
                if phase != job.status:
                    job.status = phase

        # Check for optimization iteration progress
        iter_match = self.ITER_PATTERN.search(clean)
        if iter_match:
            num = iter_match.group(1) or iter_match.group(2)
            if num:
                job.current_iteration = int(num)
            total = iter_match.group(3)
            if total:
                job.iterations = int(total)

        # Check for scores
        score_match = self.SCORE_PATTERN.search(clean)
        if score_match:
            val = score_match.group(1) or score_match.group(2) or score_match.group(3) or score_match.group(4)
            if val:
                try:
                    score = float(val)
                    if &quot;baseline&quot; in clean.lower():
                        job.baseline_score = score
                    elif &quot;evolved&quot; in clean.lower() or &quot;best&quot; in clean.lower():
                        job.current_best_score = score
                    elif &quot;improvement&quot; in clean.lower():
                        job.improvement = score
                except ValueError:
                    pass

        # Check for completion
        if &quot;evolved_skill.md&quot; in clean and &quot;Saved&quot; in clean:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now().isoformat()

        # Check for failure
        if &quot;FAILED&quot; in clean or &quot;not found&quot; in clean.lower():
            if &quot;✗&quot; in clean or &quot;Error&quot; in clean or &quot;error&quot; in clean:
                job.error = clean
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now().isoformat()

        # Persist periodically
        if len(job.logs) % 10 == 0:
            job.save_log()


# Global tracker instance
tracker = JobTracker()

    
