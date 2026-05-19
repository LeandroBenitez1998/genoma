## job_tracker.py Overview

### Key Points

- **Three core classes**: `JobStatus` (Enum with 11 job states), `EvolutionJob` (dataclass storing job metadata), and `JobTracker` (manages job lifecycle)
- **Phase-based progress tracking**: Jobs progress through 7 ordered phases (LOADING_SKILL → SAVING), with progress calculated as 0.0–1.0 based on current phase and iteration count
- **Log parsing via regex**: `JobTracker.parse_line()` detects phase transitions, scores, iterations, and completion/failure from Rich console output
- **Persistent state**: Jobs saved to JSON in `~/.hermes/evolution-logs/{job_id}.json`; logs capped at 500 lines
- **Async process management**: `JobTracker` stores `asyncio.subprocess.Process` objects per job
- **Global singleton**: Module exposes `tracker = JobTracker()` instance

### Structure / Sections Summary

| Section | Description |
|---------|-------------|
| **Imports** | Standard library: `json`, `re`, `uuid`, `asyncio`, `datetime`, `Enum`, `Path`, `dataclasses` |
| **JobStatus Enum** | 11 states: QUEUED, LOADING_SKILL, BUILDING_DATASET, VALIDATING, CONFIGURING, OPTIMIZING, EVALUATING, SAVING, COMPLETED, FAILED |
| **PHASE_ORDER** | List defining execution order for progress calculation |
| **EvolutionJob dataclass** | Fields: id, skill_name, status, iterations, current_iteration, pid, timestamps, scores (baseline/current_best/evolved), improvement, error, logs. Methods: `to_dict()`, `progress` property, `add_log()`, `save_log()` |
| **JobTracker class** | In-memory job storage (`_jobs`, `_processes` dicts). Methods: `create_job()`, `get_job()`, `get_active_jobs()`, `get_all_jobs()`, process management, `parse_line()` |
| **Log parsing** | `PHASE_PATTERNS` (15 regex patterns for phase detection), `SCORE_PATTERN`, `ITER_PATTERN` |

### Notable Entities, Patterns, and Decisions

- **Pattern**: Dataclass with `asdict()` conversion for serialization
- **Pattern**: `JobStatus` extends both `str` and `Enum` for JSON-friendly serialization
- **Pattern**: Regex-based log parsing with ANSI code stripping (`\x1b\[[0-9;]*m`)
- **Decision**: Progress within OPTIMIZING phase uses iteration ratio (`current_iteration / iterations`)
- **Decision**: Logs persisted every 10 lines for balance between durability and I/O
- **Entity**: `LOG_DIR = Path.home() / ".hermes" / "evolution-logs"` — centralized log storage
- **Entity**: Job IDs format: `{skill_name}_{YYYYMMDD_HHMMSS}_{6-char-uuid}`