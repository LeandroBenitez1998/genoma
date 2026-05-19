"""Evolution job tracking — persistent state for active and completed jobs."""

import json
import re
import uuid
import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

LOG_DIR = Path.home() / ".hermes" / "evolution-logs"


class JobStatus(str, Enum):
    QUEUED = "queued"
    LOADING_SKILL = "loading_skill"
    BUILDING_DATASET = "building_dataset"
    VALIDATING = "validating"
    CONFIGURING = "configuring"
    OPTIMIZING = "optimizing"
    EVALUATING = "evaluating"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"


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
    started_at: str = ""
    completed_at: str = ""
    baseline_score: Optional[float] = None
    current_best_score: Optional[float] = None
    evolved_score: Optional[float] = None
    improvement: Optional[float] = None
    error: str = ""
    logs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @property
    def progress(self) -> float:
        """0.0 to 1.0 progress estimate."""
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
        if self.status == JobStatus.OPTIMIZING and self.iterations > 0:
            iter_progress = self.current_iteration / self.iterations
            base = phase_idx * phase_weight
            return base + (iter_progress * phase_weight)

        return phase_idx * phase_weight

    def add_log(self, message: str):
        timestamp = datetime.now().isoformat()[:19]
        self.logs.append(f"[{timestamp}] {message}")
        # Keep last 500 lines
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]

    def save_log(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / f"{self.id}.json"
        log_file.write_text(json.dumps(self.to_dict(), indent=2))


class JobTracker:
    def __init__(self):
        self._jobs: dict[str, EvolutionJob] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    def create_job(self, skill_name: str, iterations: int) -> EvolutionJob:
        job_id = f"{skill_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        job = EvolutionJob(
            id=job_id,
            skill_name=skill_name,
            iterations=iterations,
            started_at=datetime.now().isoformat(),
        )
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[EvolutionJob]:
        return self._jobs.get(job_id)

    def get_active_jobs(self) -> list[EvolutionJob]:
        return [
            j for j in self._jobs.values()
            if j.status not in (JobStatus.COMPLETED, JobStatus.FAILED)
        ]

    def get_all_jobs(self, limit: int = 50) -> list[EvolutionJob]:
        sorted_jobs = sorted(
            self._jobs.values(),
            key=lambda j: j.started_at,
            reverse=True,
        )
        return sorted_jobs[:limit]

    def set_process(self, job_id: str, process: asyncio.subprocess.Process):
        self._processes[job_id] = process

    def get_process(self, job_id: str) -> Optional[asyncio.subprocess.Process]:
        return self._processes.get(job_id)

    def cleanup_process(self, job_id: str):
        self._processes.pop(job_id, None)

    # ── Log parsing ─────────────────────────────────────────────────

    # Patterns to detect phase changes from Rich output
    PHASE_PATTERNS = [
        (r"Loaded:.*\.md", JobStatus.LOADING_SKILL),
        (r"Building evaluation dataset", JobStatus.BUILDING_DATASET),
        (r"Generated.*synthetic examples", JobStatus.BUILDING_DATASET),
        (r"Mined.*examples from session", JobStatus.BUILDING_DATASET),
        (r"Loaded golden dataset", JobStatus.BUILDING_DATASET),
        (r"Validating baseline constraints", JobStatus.VALIDATING),
        (r"Configuring optimizer", JobStatus.CONFIGURING),
        (r"Running GEPA optimization", JobStatus.OPTIMIZING),
        (r"Running MIPROv2", JobStatus.OPTIMIZING),
        (r"Optimization completed", JobStatus.OPTIMIZING),
        (r"Validating evolved skill", JobStatus.EVALUATING),
        (r"Evaluating on holdout", JobStatus.EVALUATING),
        (r"Evolution Results", JobStatus.SAVING),
        (r"Saved.*to output", JobStatus.SAVING),
        (r"✓ Skill evolved", JobStatus.COMPLETED),
    ]

    # Pattern to extract scores
    SCORE_PATTERN = re.compile(r"baseline[=_:\s]+(\d+\.?\d*)|evolved[=_:\s]+(\d+\.?\d*)|score[=_:\s]+(\d+\.?\d*)|improvement[=_:\s]+([+-]?\d+\.?\d*)", re.IGNORECASE)

    # Pattern to extract iteration number
    ITER_PATTERN = re.compile(r"iteration[=:\s]+(\d+)|eval[=:\s#]+(\d+)/(\d+)", re.IGNORECASE)

    def parse_line(self, job: EvolutionJob, line: str):
        """Parse a log line and update job state."""
        # Strip ANSI codes
        clean = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
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
                    if "baseline" in clean.lower():
                        job.baseline_score = score
                    elif "evolved" in clean.lower() or "best" in clean.lower():
                        job.current_best_score = score
                    elif "improvement" in clean.lower():
                        job.improvement = score
                except ValueError:
                    pass

        # Check for completion
        if "evolved_skill.md" in clean and "Saved" in clean:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now().isoformat()

        # Check for failure
        if "FAILED" in clean or "not found" in clean.lower():
            if "✗" in clean or "Error" in clean or "error" in clean:
                job.error = clean
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now().isoformat()

        # Persist periodically
        if len(job.logs) % 10 == 0:
            job.save_log()


# Global tracker instance
tracker = JobTracker()
