"""Hermes Evolution Dashboard — FastAPI Backend

Bridges the Next.js frontend to the hermes-agent-self-evolution Python modules.
Exposes REST endpoints + WebSocket streaming for real-time evolution monitoring.
"""

import json
import os
import sys
import shutil
import asyncio
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .skill_registry import get_registry
from .job_tracker import tracker, EvolutionJob, JobStatus

# ── Paths ──────────────────────────────────────────────────────────
HERMES_REPO = Path(os.environ.get("HERMES_AGENT_REPO", Path.home() / ".hermes" / "hermes-agent"))

# Evolution dir: env var > sibling > home
_env_ev = os.environ.get("EVOLUTION_DIR", "")
if _env_ev:
    EVOLUTION_DIR = Path(_env_ev)
else:
    _sibling = Path(__file__).parent.parent.parent / "hermes-agent-self-evolution"
    _home = Path.home() / ".hermes" / "hermes-agent-self-evolution"
    EVOLUTION_DIR = _sibling if _sibling.exists() else _home

SKILLS_DIR = HERMES_REPO / "skills"
MEMORY_DIR = Path.home() / ".hermes" / "memory"
DATASETS_DIR = Path.home() / ".hermes" / "datasets"

# ── Skill Registry (lazy loaded) ────────────────────────────────
_skill_registry = None

def get_skill_registry():
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = get_registry()
    return _skill_registry

SESSIONS_DIR = Path.home() / ".hermes" / "sessions"

# ── Python executable ──────────────────────────────────────────────
def _find_python() -> str:
    """Find the best Python executable (supports evolution modules)."""
    # 1. Env var override
    env_py = os.environ.get("PYTHON", "")
    if env_py and Path(env_py).exists():
        return env_py

    # 2. System python3.12 (where dspy is installed)
    for candidate in ["/usr/bin/python3", "python3.12", "python3.11", "python3"]:
        try:
            result = subprocess.run(
                [candidate, "-c", "import dspy; print('ok')"],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    # 3. Fallback
    return sys.executable

PYTHON_BIN = _find_python()

app = FastAPI(title="Hermes Evolution API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── WebSocket manager ──────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# ── Models ─────────────────────────────────────────────────────────

class SkillInfo(BaseModel):
    name: str
    path: str
    description: str
    size: int
    last_modified: str
    source: str = "skill"  # "skill" or "description"

class EvolveRequest(BaseModel):
    skill_name: str
    iterations: int = 3
    eval_source: str = "synthetic"
    dataset_size: int = 10

class MemoryEntry(BaseModel):
    key: str
    value: str
    source: str
    timestamp: str

class RunMetrics(BaseModel):
    skill_name: str
    timestamp: str
    baseline_score: float
    evolved_score: float
    improvement: float
    elapsed_seconds: float
    constraints_passed: bool

# ── Helpers ────────────────────────────────────────────────────────

def _normalize_metrics(raw: dict) -> dict:
    """Normalize metrics.json from different versions of evolve scripts.

    Supports:
    - evolve_skill.py format: skill_name, baseline_score, evolved_score, improvement
    - evolve_now.py format: skill, original_size, evolved_size, diff_lines
    """
    m = dict(raw)  # shallow copy

    # Normalize skill name key
    if "skill" in m and "skill_name" not in m:
        m["skill_name"] = m["skill"]

    # Normalize scores
    if "baseline_score" not in m:
        if "original_size" in m and m["original_size"] > 0:
            # Derive a pseudo-score from size reduction (lower = more concise = better)
            ratio = m.get("evolved_size", m["original_size"]) / m["original_size"]
            m["baseline_score"] = 0.5  # placeholder
            m["evolved_score"] = min(1.0, 0.5 + (1 - ratio) * 0.3)
            m["improvement"] = m["evolved_score"] - m["baseline_score"]
        else:
            m["baseline_score"] = 0.0
            m["evolved_score"] = 0.0
            m["improvement"] = 0.0

    # Normalize constraints_passed
    if "constraints_passed" not in m:
        m["constraints_passed"] = m.get("diff_lines", 0) > 0

    # Normalize elapsed
    if "elapsed_seconds" not in m:
        m["elapsed_seconds"] = 0.0

    # Normalize iterations
    if "iterations" not in m:
        m["iterations"] = 3

    return m

def _find_skill_file(skill_name: str) -> Optional[Path]:
    """Find a SKILL.md by name, searching recursively."""
    if not SKILLS_DIR.exists():
        return None

    # Direct path
    direct = SKILLS_DIR / skill_name / "SKILL.md"
    if direct.exists():
        return direct

    # Recursive search
    for f in SKILLS_DIR.rglob("SKILL.md"):
        if f.parent.name == skill_name:
            return f

    return None

def _parse_skill_content(skill_file: Path) -> dict:
    """Parse a skill file into frontmatter + body."""
    content = skill_file.read_text(encoding="utf-8", errors="replace")
    frontmatter = {}
    body = content

    if content.startswith("---"):
        try:
            import yaml
            end = content.index("---", 3)
            frontmatter = yaml.safe_load(content[3:end]) or {}
            body = content[end + 3:].strip()
        except Exception:
            pass

    return {
        "frontmatter": frontmatter,
        "body": body,
        "raw": content,
    }

# ── SKILLS endpoints ───────────────────────────────────────────────

class ToggleSkillRequest(BaseModel):
    provider: str
    skill_name: str
    enabled: bool

@app.get("/api/skills/providers")
async def list_providers():
    """Lista todos los proveedores de skills detectados con sus estadísticas"""
    try:
        providers = get_skill_registry().get_providers()
        return {"status": "ok", "providers": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/skills/provider/{provider_name}")
async def get_provider_skills(provider_name: str):
    """Lista todas las skills de un proveedor específico"""
    try:
        providers = get_skill_registry().get_providers()
        for p in providers:
            if p["name"] == provider_name:
                return {"status": "ok", "provider": p}
        raise HTTPException(status_code=404, detail=f"Proveedor '{provider_name}' no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/skills/refresh")
async def refresh_skills():
    """Fuerza un re-escaneo de skills (útil para desarrollo)"""
    try:
        global _skill_registry
        _skill_registry = get_registry().rescan()
        providers = _skill_registry.get_providers()
        return {"status": "ok", "providers": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/skills/toggle")
async def toggle_skill(request: ToggleSkillRequest):
    """Activa o desactiva una skill"""
    try:
        get_skill_registry().toggle_provider_skill(request.provider, request.skill_name, request.enabled)
        return {"status": "ok", "enabled": request.enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/skills/global/{skill_name}")
async def delete_global_skill(skill_name: str):
    """Elimina una skill GLOBALMENTE (de global_skills/ y todos los symlinks)."""
    try:
        registry = get_registry()
        target_gid = None
        target_skill = None
        for gid, s in registry.global_skills.items():
            if s.name == skill_name and not s.is_fork:
                target_gid = gid
                target_skill = s
                break
        
        if not target_skill:
            raise HTTPException(status_code=404, detail="Skill global no encontrada o es un fork")
        canonical = Path(target_skill.canonical_path)
        
        # 1. Eliminar symlinks en todos los providers PRIMERO
        for provider_name, src_dir in registry.PROVIDER_SOURCES.items():
            if not src_dir.exists():
                continue
            link = src_dir / skill_name
            if link.exists() and link.is_symlink():
                try:
                    if link.resolve() == canonical:
                        link.unlink()
                except Exception:
                    pass
        
        # 2. Eliminar directorio canónico
        if canonical.exists() and canonical.is_dir():
            shutil.rmtree(canonical)
        
        keys_to_delete = [k for k, v in registry.provider_index.items() if v == target_gid]
        for k in keys_to_delete:
            del registry.provider_index[k]
        del registry.global_skills[target_gid]
        
        registry.save()
        return {"status": "ok", "message": f"Skill '{skill_name}' eliminada globalmente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/skills/{provider}/{skill_name}")
async def delete_skill(provider: str, skill_name: str):
    """Elimina una skill de un provider específico (desenlaza, pero preserva la skill global)."""
    try:
        registry = get_registry()
        key = f"{provider}.{skill_name}"
        if key not in registry.provider_index:
            raise HTTPException(status_code=404, detail="Skill no encontrada para ese provider")
        
        gid = registry.provider_index[key]
        if gid not in registry.global_skills:
            del registry.provider_index[key]
            registry.save()
            return {"status": "ok", "message": f"Enlace eliminado (skill global no existía)"}
        
        skill = registry.global_skills[gid]
        skill.providers = [p for p in skill.providers if p['name'] != provider]
        del registry.provider_index[key]
        registry.save()
        return {"status": "ok", "message": f"Skill '{skill_name}' desenlazada de '{provider}'"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/skills/{skill_name}")
async def get_skill(skill_name: str):
    """Get full skill content + metadata."""
    skill_file = _find_skill_file(skill_name)
    if not skill_file:
        raise HTTPException(404, f"Skill '{skill_name}' not found")

    parsed = _parse_skill_content(skill_file)
    return {
        "name": skill_name,
        "path": str(skill_file.relative_to(HERMES_REPO)),
        "frontmatter": parsed["frontmatter"],
        "body": parsed["body"],
        "raw": parsed["raw"],
        "size": len(parsed["raw"]),
    }

@app.get("/api/evolution/evolvable")
async def list_evolvable_skills(provider: Optional[str] = None):
    """List skills that can be evolved, grouped by provider (Hermes, Claude Code, OpenCode)."""
    from .skill_registry import get_registry
    registry = get_registry()

    providers = registry.get_providers()
    result = []
    for p in providers:
        if provider and p["name"] != provider:
            continue
        # Only include providers with evolvable skills (have a SKILL.md)
        evolvable = [
            s for s in p["skills"]
            if s["enabled"] and not s.get("is_fork")
        ]
        if evolvable:
            result.append({
                "provider": p["name"],
                "total": p["total"],
                "enabled": p["enabled"],
                "skills": evolvable,
            })

    # Sort by total skills desc
    result.sort(key=lambda x: x["total"], reverse=True)
    return {"status": "ok", "providers": result}


@app.get("/api/evolution/runs")
async def list_evolution_runs():
    """List all evolution runs — from metrics.json AND job tracker."""
    output_dir = EVOLUTION_DIR / "output"
    all_runs = []
    seen_skills = set()

    # 1. From metrics.json files (successful runs)
    if output_dir.exists():
        for skill_dir in output_dir.iterdir():
            if skill_dir.is_dir() and skill_dir.name != "skills":
                for run_dir in skill_dir.iterdir():
                    mf = run_dir / "metrics.json"
                    if mf.exists():
                        try:
                            data = _normalize_metrics(json.loads(mf.read_text()))
                            data.setdefault("run_dir", run_dir.name)
                            all_runs.append(data)
                            seen_skills.add(skill_dir.name)
                        except Exception:
                            pass

    # 2. From job tracker (completed/failed runs without metrics.json)
    for job in tracker.get_all_jobs(limit=200):
        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            # Check if we already have metrics for this skill
            has_metrics = any(
                r.get("skill_name") == job.skill_name
                and r.get("timestamp", "").replace("_", "").startswith(
                    job.started_at.replace("-", "").replace(":", "").replace("T", "")[:8]
                )
                for r in all_runs
            )
            if not has_metrics:
                all_runs.append({
                    "skill_name": job.skill_name,
                    "timestamp": job.started_at.replace("-", "").replace(":", "").replace("T", "_")[:15],
                    "iterations": job.iterations,
                    "baseline_score": job.baseline_score or 0.0,
                    "evolved_score": job.evolved_score or 0.0,
                    "improvement": job.improvement or 0.0,
                    "elapsed_seconds": 0.0,
                    "constraints_passed": job.status == JobStatus.COMPLETED,
                    "status": job.status.value,
                    "error": job.error,
                })

    return sorted(all_runs, key=lambda r: r.get("timestamp", ""), reverse=True)

# ── EVOLUTION endpoints ────────────────────────────────────────────

@app.get("/api/skills/{skill_name}/evolution-history")
async def skill_history(skill_name: str):
    """Get evolution run history for a skill."""
    output_dir = EVOLUTION_DIR / "output" / skill_name
    runs = []

    if output_dir.exists():
        for run_dir in sorted(output_dir.iterdir(), reverse=True):
            metrics_file = run_dir / "metrics.json"
            if metrics_file.exists():
                try:
                    data = json.loads(metrics_file.read_text())
                    data["run_dir"] = str(run_dir.name)
                    runs.append(_normalize_metrics(data))
                except Exception:
                    pass

    # Also add from job tracker
    for job in tracker.get_all_jobs(limit=50):
        if job.skill_name == skill_name and job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            has_metrics = any(r.get("timestamp", "").startswith(job.started_at[:10]) for r in runs)
            if not has_metrics:
                runs.append({
                    "skill_name": job.skill_name,
                    "timestamp": job.started_at.replace("-", "").replace(":", "").replace("T", "_")[:15],
                    "iterations": job.iterations,
                    "baseline_score": job.baseline_score or 0.0,
                    "evolved_score": job.evolved_score or 0.0,
                    "improvement": job.improvement or 0.0,
                    "elapsed_seconds": 0.0,
                    "constraints_passed": job.status == JobStatus.COMPLETED,
                    "status": job.status.value,
                    "error": job.error,
                })

    return runs

@app.get("/api/skills/{skill_name}/evolution/{run_dir}/diff")
async def skill_diff(skill_name: str, run_dir: str):
    """Get baseline vs evolved skill content for a specific run."""
    skill_path = EVOLUTION_DIR / "output" / skill_name

    # Support "latest" keyword
    if run_dir == "latest":
        if not skill_path.exists():
            raise HTTPException(404, f"No evolution runs found for skill '{skill_name}'")
        runs = sorted(
            [d for d in skill_path.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        if not runs:
            raise HTTPException(404, f"No evolution runs found for skill '{skill_name}'")
        run_path = runs[0]
    else:
        run_path = skill_path / run_dir

    if not run_path.exists():
        raise HTTPException(404, f"Run '{run_dir}' not found for skill '{skill_name}'")

    baseline_file = run_path / "baseline_skill.md"
    evolved_file = run_path / "evolved_skill.md"
    metrics_file = run_path / "metrics.json"

    result = {
        "skill_name": skill_name,
        "run_dir": run_dir,
        "baseline": None,
        "evolved": None,
        "metrics": None,
    }

    if baseline_file.exists():
        result["baseline"] = baseline_file.read_text(encoding="utf-8", errors="replace")
    if evolved_file.exists():
        result["evolved"] = evolved_file.read_text(encoding="utf-8", errors="replace")
    if metrics_file.exists():
        try:
            result["metrics"] = json.loads(metrics_file.read_text())
        except Exception:
            pass

    return result


@app.post("/api/evolution/validate")
async def validate_evolution_endpoint(skill_name: str):
    """Validate latest evolution with LLM Judge + holdout dataset."""
    import subprocess as sp

    validate_path = Path(__file__).parent / "validate_evolution.py"
    cmd = [PYTHON_BIN, "-u", str(validate_path), "--skill", skill_name]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        result = sp.run(cmd, capture_output=True, text=True, timeout=180, env=env)
        runs = sorted(
            [d for d in (EVOLUTION_DIR / "output" / skill_name).iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime, reverse=True,
        )
        if runs:
            rp = runs[0] / "validation_report.json"
            if rp.exists():
                return json.loads(rp.read_text())
        return {"skill_name": skill_name, "final_verdict": "FAIL ❌",
                "error": "No report generated", "stdout": result.stdout[-500:]}
    except sp.TimeoutExpired:
        raise HTTPException(504, "Validation timed out (>3 min)")
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/evolution/validate/{skill_name}")
async def get_validation_report(skill_name: str):
    """Get latest validation report for a skill."""
    output_dir = EVOLUTION_DIR / "output" / skill_name
    if not output_dir.exists():
        raise HTTPException(404, f"No evolution output for '{skill_name}'")
    runs = sorted([d for d in output_dir.iterdir() if d.is_dir()],
                  key=lambda d: d.stat().st_mtime, reverse=True)
    for run in runs:
        rp = run / "validation_report.json"
        if rp.exists():
            return json.loads(rp.read_text())
    raise HTTPException(404, f"No validation report for '{skill_name}'")


@app.post("/api/evolution/start")
async def start_evolution(req: EvolveRequest):
    """Start an evolution run with full job tracking."""

    # Check for existing active jobs for this skill
    active = tracker.get_active_jobs()
    for job in active:
        if job.skill_name == req.skill_name:
            return {
                "error": f"Evolution already running for '{req.skill_name}'",
                "job_id": job.id,
                "status": job.status.value,
            }

    # Create tracked job
    job = tracker.create_job(req.skill_name, req.iterations)
    job.add_log(f"Starting evolution for skill: {req.skill_name}")
    job.add_log(f"Iterations: {req.iterations}, Source: {req.eval_source}")

    # Build command — use SDD evolution engine
    sdd_evolve_path = Path(__file__).parent / "sdd_evolve.py"
    cmd = [
        "/usr/bin/python3", "-u", str(sdd_evolve_path),
        "--skill", req.skill_name,
        "--iterations", str(req.iterations),
        "--eval-source", req.eval_source,
    ]

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["HERMES_AGENT_REPO"] = str(HERMES_REPO)
    env["TERM"] = "dumb"

    # ── Provider selection: Ollama preferred when available ───────────
    def _ollama_up() -> bool:
        import urllib.request
        try:
            with urllib.request.urlopen("http://localhost:11434/v1/models", timeout=2) as r:
                return r.status == 200
        except Exception:
            return False

    _dotenv = dotenv_values(str(Path.home() / ".hermes" / ".env"))
    for key in ("OLLAMA_API_BASE", "SDD_OLLAMA_MODEL", "SDD_EVOLVE_MODEL"):
        if key in os.environ:
            env[key] = os.environ[key]
        elif _dotenv.get(key):
            env[key] = _dotenv[key]

    if _ollama_up():
        # Local Ollama is alive — use it regardless of stale cloud keys in .env
        base = env.get("OLLAMA_API_BASE", "http://localhost:11434/v1")
        if not base.rstrip("/").endswith("/v1"):
            base = base.rstrip("/") + "/v1"
        env["OPENAI_BASE_URL"] = base
        env["OPENAI_API_KEY"] = "ollama"
        env.setdefault("SDD_EVOLVE_MODEL", env.get("SDD_OLLAMA_MODEL", "gemma4:31b-cloud"))
        job.add_log("Provider: Ollama local (gemma4:31b-cloud)")
    else:
        # Forward cloud keys only when Ollama is NOT available
        for key in ("OPENROUTER_API_KEY", "NOUS_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            if key in os.environ:
                env[key] = os.environ[key]
            elif _dotenv.get(key):
                env[key] = _dotenv[key]
        env.setdefault("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(Path(__file__).parent),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = f"Failed to start process: {e}"
        job.completed_at = datetime.now().isoformat()
        job.save_log()
        return {"error": job.error, "job_id": job.id}

    job.pid = process.pid
    job.status = JobStatus.LOADING_SKILL
    tracker.set_process(job.id, process)

    # Stream and parse output
    async def stream_output():
        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").strip()

                if text:
                    # Parse line for structured updates
                    tracker.parse_line(job, text)

                    # Broadcast to WebSocket clients
                    await manager.broadcast({
                        "type": "evolution_log",
                        "job_id": job.id,
                        "skill": req.skill_name,
                        "status": job.status.value,
                        "progress": job.progress,
                        "iteration": job.current_iteration,
                        "total_iterations": job.iterations,
                        "message": text,
                        "timestamp": datetime.now().isoformat(),
                    })

            # Process ended
            await process.wait()
            if job.status not in (JobStatus.COMPLETED, JobStatus.FAILED):
                if process.returncode == 0:
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now().isoformat()
                    job.add_log("Process completed successfully")
                else:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now().isoformat()
                    job.error = f"Process exited with code {process.returncode}"
                    job.add_log(f"Process failed: {job.error}")

            # Try to load final metrics from output
            output_dir = EVOLUTION_DIR / "output" / req.skill_name
            if output_dir.exists():
                latest_run = max(
                    [d for d in output_dir.iterdir() if d.is_dir()],
                    key=lambda d: d.stat().st_mtime,
                    default=None,
                )
                if latest_run:
                    mf = latest_run / "metrics.json"
                    if mf.exists():
                        try:
                            metrics = json.loads(mf.read_text())
                            job.baseline_score = metrics.get("baseline_score")
                            job.evolved_score = metrics.get("evolved_score")
                            job.improvement = metrics.get("improvement")
                        except Exception:
                            pass

            job.save_log()
            tracker.cleanup_process(job.id)

            # Broadcast completion
            await manager.broadcast({
                "type": "evolution_complete",
                "job_id": job.id,
                "skill": req.skill_name,
                "status": job.status.value,
                "baseline_score": job.baseline_score,
                "evolved_score": job.evolved_score,
                "improvement": job.improvement,
                "timestamp": datetime.now().isoformat(),
            })

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now().isoformat()
            job.save_log()
            tracker.cleanup_process(job.id)

    asyncio.create_task(stream_output())

    return {
        "job_id": job.id,
        "skill": req.skill_name,
        "status": job.status.value,
        "iterations": req.iterations,
        "pid": process.pid,
    }

# ── Job tracking endpoints ────────────────────────────────────────────

@app.get("/api/jobs")
async def list_jobs(active_only: bool = False, limit: int = 50):
    """List evolution jobs."""
    if active_only:
        jobs = tracker.get_active_jobs()
    else:
        jobs = tracker.get_all_jobs(limit)
    return [j.to_dict() for j in jobs]

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get detailed job status including logs."""
    job = tracker.get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found")
    return job.to_dict()

@app.get("/api/jobs/{job_id}/logs")
async def get_job_logs(job_id: str, since: int = 0):
    """Get job logs (optionally only lines after index `since`)."""
    job = tracker.get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found")
    return {
        "job_id": job_id,
        "total_lines": len(job.logs),
        "logs": job.logs[since:],
        "status": job.status.value,
        "progress": job.progress,
    }

@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running evolution job."""
    job = tracker.get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found")

    process = tracker.get_process(job_id)
    if process:
        try:
            process.terminate()
            await process.wait()
        except Exception:
            pass
        tracker.cleanup_process(job_id)

    job.status = JobStatus.FAILED
    job.error = "Cancelled by user"
    job.completed_at = datetime.now().isoformat()
    job.save_log()

    await manager.broadcast({
        "type": "evolution_cancelled",
        "job_id": job_id,
        "skill": job.skill_name,
    })

    return {"status": "cancelled", "job_id": job_id}

@app.get("/api/evolution/{skill_name}/output/{run_id}")
async def get_run_output(skill_name: str, run_id: str):
    """Get evolved vs baseline skill diff for a specific run."""
    run_dir = EVOLUTION_DIR / "output" / skill_name / run_id

    if not run_dir.exists():
        raise HTTPException(404, "Run not found")

    result = {}

    for f in ["evolved_skill.md", "baseline_skill.md", "evolved_FAILED.md"]:
        fp = run_dir / f
        if fp.exists():
            result[f.replace(".md", "")] = fp.read_text(encoding="utf-8", errors="replace")

    metrics_file = run_dir / "metrics.json"
    if metrics_file.exists():
        raw = json.loads(metrics_file.read_text())
        result["metrics"] = _normalize_metrics(raw)

    return result

# ── DATASET endpoints ──────────────────────────────────────────────

@app.get("/api/datasets")
async def list_datasets():
    """List all eval datasets — from datasets/ dir AND evolution output."""
    datasets = []

    for base in [DATASETS_DIR, EVOLUTION_DIR / "datasets", EVOLUTION_DIR / "output"]:
        if not base.exists():
            continue
        for skill_dir in base.iterdir():
            if skill_dir.is_dir():
                splits = {}
                for split in ["train.jsonl", "val.jsonl", "holdout.jsonl"]:
                    fp = skill_dir / split
                    if fp.exists():
                        count = sum(1 for _ in open(fp))
                        splits[split.replace(".jsonl", "")] = count
                if splits:
                    datasets.append({
                        "skill": skill_dir.name,
                        "path": str(skill_dir),
                        "splits": splits,
                        "total": sum(splits.values()),
                    })

    return datasets

@app.get("/api/datasets/{skill_name}")
async def get_dataset(skill_name: str):
    """Get dataset examples for a skill."""
    for base in [DATASETS_DIR, EVOLUTION_DIR / "datasets", EVOLUTION_DIR / "output"]:
        dataset_dir = base / skill_name
        if dataset_dir.exists():
            result = {}
            for split in ["train", "val", "holdout"]:
                fp = dataset_dir / f"{split}.jsonl"
                if fp.exists():
                    examples = []
                    for line in open(fp):
                        try:
                            examples.append(json.loads(line))
                        except Exception:
                            pass
                    result[split] = examples
            return result

    raise HTTPException(404, f"No dataset found for '{skill_name}'")

@app.get("/api/datasets/{skill_name}/sessions")
async def import_sessions(skill_name: str, source: str = "all", max_examples: int = 50):
    """Import and filter external sessions for dataset building."""
    cmd = [
        PYTHON_BIN, "-m", "evolution.core.external_importers",
        "--source", source,
        "--skill", skill_name,
        "--max-examples", str(max_examples),
        "--dry-run",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(EVOLUTION_DIR)
    env["HERMES_AGENT_REPO"] = str(HERMES_REPO)

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(EVOLUTION_DIR), env=env)

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }

# ── MEMORY endpoints ───────────────────────────────────────────────

@app.get("/api/memory")
async def list_memory():
    """List all stored memories."""
    memories = []

    # Check .hermes/memory directory
    if MEMORY_DIR.exists():
        for f in sorted(MEMORY_DIR.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                memories.append({
                    "key": f.stem,
                    "data": data,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
            except Exception:
                memories.append({
                    "key": f.stem,
                    "data": f.read_text()[:200],
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })

    # Also check SOUL.md memory section
    soul_path = Path.home() / ".hermes" / "SOUL.md"
    if soul_path.exists():
        content = soul_path.read_text(encoding="utf-8", errors="replace")
        if "MEMORY" in content:
            memories.append({
                "key": "SOUL_MEMORY",
                "source": "SOUL.md",
                "size": len(content),
            })

    return memories

# ── GRAPH endpoint (vis.js format — same as graphify) ─────────────────

COMMUNITY_COLORS = [
    "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
]

@app.get("/api/graph")
async def get_graph():
    """Generate a vis.js knowledge graph from skills, memory, and evolution runs.

    Format matches graphify's export: nodes + edges for vis-network.
    """
    nodes = {}
    edges = []
    communities = {}  # community_id -> [node_ids]

    # ── 1. Skills as nodes ────────────────────────────────────────
    skill_nodes = {}
    if SKILLS_DIR.exists():
        category_map = {}  # category_dir -> community_id
        cat_counter = 0

        for skill_file in sorted(SKILLS_DIR.rglob("SKILL.md")):
            skill_name = skill_file.parent.name
            category = skill_file.parent.parent.name if skill_file.parent.parent != SKILLS_DIR else "root"

            # Assign community by category
            if category not in category_map:
                category_map[category] = cat_counter
                communities[cat_counter] = []
                cat_counter += 1
            cid = category_map[category]

            # Read skill
            content = skill_file.read_text(encoding="utf-8", errors="replace")
            stat = skill_file.stat()
            desc = ""
            if content.startswith("---"):
                try:
                    import yaml
                    end = content.index("---", 3)
                    fm = yaml.safe_load(content[3:end])
                    desc = (fm.get("description") or "")[:80]
                except Exception:
                    pass

            node_id = f"skill:{skill_name}"
            deg = 0  # will update after edges
            nodes[node_id] = {
                "id": node_id,
                "label": skill_name,
                "color": {"background": COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)], "border": COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)], "highlight": {"background": "#ffffff", "border": COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]}},
                "size": 15,
                "font": {"size": 11, "color": "#ffffff"},
                "title": f"{skill_name}\n{desc}",
                "community": cid,
                "community_name": category,
                "source_file": str(skill_file.relative_to(HERMES_REPO)),
                "file_type": "skill",
                "degree": 0,
            }
            communities[cid].append(node_id)
            skill_nodes[skill_name] = node_id

            # Edge: skill -> category
            cat_node_id = f"cat:{category}"
            if cat_node_id not in nodes:
                nodes[cat_node_id] = {
                    "id": cat_node_id,
                    "label": category,
                    "color": {"background": "#555555", "border": "#555555", "highlight": {"background": "#ffffff", "border": "#555555"}},
                    "size": 22,
                    "font": {"size": 13, "color": "#ffffff"},
                    "title": f"Category: {category}",
                    "community": cid,
                    "community_name": category,
                    "source_file": "",
                    "file_type": "category",
                    "degree": 0,
                }
            edges.append({
                "from": node_id,
                "to": cat_node_id,
                "label": "belongs_to",
                "title": "belongs_to",
                "dashes": False,
                "width": 1,
                "color": {"opacity": 0.4},
                "confidence": "STRUCTURAL",
            })

    # ── 2. Evolution runs as edges between skill variants ─────────
    output_dir = EVOLUTION_DIR / "output"
    if output_dir.exists():
        for skill_dir in output_dir.iterdir():
            if skill_dir.is_dir() and skill_dir.name != "skills":
                for run_dir in skill_dir.iterdir():
                    mf = run_dir / "metrics.json"
                    if mf.exists():
                        try:
                            data = json.loads(mf.read_text())
                            evolved_id = f"evolved:{skill_dir.name}:{run_dir.name}"
                            baseline_id = skill_nodes.get(skill_dir.name)

                            nodes[evolved_id] = {
                                "id": evolved_id,
                                "label": f"{skill_dir.name} ✦",
                                "color": {"background": "#22c55e", "border": "#22c55e", "highlight": {"background": "#ffffff", "border": "#22c55e"}},
                                "size": 10 + (data.get("improvement", 0) * 100),
                                "font": {"size": 9, "color": "#a0a0a0"},
                                "title": f"Evolved: {skill_dir.name}\nScore: {data.get('evolved_score', 0):.2f}\nImprovement: {data.get('improvement', 0)*100:.1f}%",
                                "community": 0,
                                "community_name": "evolved",
                                "source_file": str(run_dir),
                                "file_type": "evolution",
                                "degree": 1,
                            }

                            if baseline_id:
                                edges.append({
                                    "from": baseline_id,
                                    "to": evolved_id,
                                    "label": "evolved_to",
                                    "title": f"+{(data.get('improvement', 0)*100):.1f}%",
                                    "dashes": True,
                                    "width": 2,
                                    "color": {"opacity": 0.8},
                                    "confidence": "EXTRACTED",
                                })
                        except Exception:
                            pass

    # ── 3. Memory entries as nodes ────────────────────────────────
    if MEMORY_DIR.exists():
        mem_cid = cat_counter
        communities[mem_cid] = []
        for f in sorted(MEMORY_DIR.glob("*.json")):
            try:
                mem_data = json.loads(f.read_text())
                mem_id = f"memory:{f.stem}"
                nodes[mem_id] = {
                    "id": mem_id,
                    "label": f.stem,
                    "color": {"background": "#8b5cf6", "border": "#8b5cf6", "highlight": {"background": "#ffffff", "border": "#8b5cf6"}},
                    "size": 12,
                    "font": {"size": 10, "color": "#c4b5fd"},
                    "title": f"Memory: {f.stem}",
                    "community": mem_cid,
                    "community_name": "memory",
                    "source_file": str(f),
                    "file_type": "memory",
                    "degree": 0,
                }
                communities[mem_cid].append(mem_id)
            except Exception:
                pass

    # ── 4. SOUL.md as hub node ────────────────────────────────────
    soul_path = Path.home() / ".hermes" / "SOUL.md"
    if soul_path.exists():
        soul_id = "soul:SOUL.md"
        nodes[soul_id] = {
            "id": soul_id,
            "label": "SOUL.md",
            "color": {"background": "#eab308", "border": "#eab308", "highlight": {"background": "#ffffff", "border": "#eab308"}},
            "size": 25,
            "font": {"size": 13, "color": "#ffffff"},
            "title": "Hermes Soul — Core identity and memory",
            "community": cat_counter + 1,
            "community_name": "core",
            "source_file": str(soul_path),
            "file_type": "core",
            "degree": 0,
        }

    # ── Calculate degrees and node sizes ──────────────────────────
    for e in edges:
        if e["from"] in nodes:
            nodes[e["from"]]["degree"] = nodes[e["from"]].get("degree", 0) + 1
        if e["to"] in nodes:
            nodes[e["to"]]["degree"] = nodes[e["to"]].get("degree", 0) + 1

    max_deg = max((n.get("degree", 0) for n in nodes.values()), default=1) or 1
    for n in nodes.values():
        deg = n.get("degree", 0)
        n["size"] = round(10 + 30 * (deg / max_deg), 1)
        n["font"]["size"] = 12 if deg >= max_deg * 0.15 else 0

    # ── Legend ────────────────────────────────────────────────────
    legend = []
    for cid, label in enumerate(list(category_map.keys()) if 'category_map' in dir() else []):
        legend.append({
            "cid": cid,
            "color": COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)],
            "label": label,
            "count": len(communities.get(cid, [])),
        })

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "legend": legend,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "communities": len(communities),
            "skills": len(skill_nodes),
        },
    }

# ── METRICS endpoints ──────────────────────────────────────────────

@app.get("/api/metrics")
async def get_metrics():
    """Aggregate metrics across all evolution runs."""
    output_dir = EVOLUTION_DIR / "output"

    all_runs = []
    if output_dir.exists():
        for skill_dir in output_dir.iterdir():
            if skill_dir.is_dir():
                for run_dir in skill_dir.iterdir():
                    mf = run_dir / "metrics.json"
                    if mf.exists():
                        try:
                            raw = json.loads(mf.read_text())
                            all_runs.append(_normalize_metrics(raw))
                        except Exception:
                            pass

    if not all_runs:
        return {
            "total_runs": 0,
            "skills_evolved": 0,
            "avg_improvement": 0,
            "best_improvement": 0,
            "total_time_seconds": 0,
            "avg_time_seconds": 0,
            "success_rate": 0,
            "runs": [],
        }

    improvements = [r.get("improvement", 0) for r in all_runs]
    times = [r.get("elapsed_seconds", 0) for r in all_runs]
    passed = sum(1 for r in all_runs if r.get("constraints_passed", False))
    skills = set(r.get("skill_name", "unknown") for r in all_runs)

    return {
        "total_runs": len(all_runs),
        "skills_evolved": len(skills),
        "avg_improvement": sum(improvements) / len(improvements) if improvements else 0,
        "best_improvement": max(improvements) if improvements else 0,
        "total_time_seconds": sum(times),
        "avg_time_seconds": sum(times) / len(times) if times else 0,
        "success_rate": passed / len(all_runs) if all_runs else 0,
        "runs": sorted(all_runs, key=lambda r: r.get("timestamp", ""), reverse=True)[:20],
    }

# ── CONSTRAINTS endpoints ──────────────────────────────────────────

@app.get("/api/constraints/validate/{skill_name}")
async def validate_skill(skill_name: str):
    """Validate a skill against all constraints."""
    skill_file = _find_skill_file(skill_name)
    if not skill_file:
        raise HTTPException(404, f"Skill '{skill_name}' not found")

    content = skill_file.read_text(encoding="utf-8", errors="replace")

    # Try evolution module first
    try:
        sys.path.insert(0, str(EVOLUTION_DIR))
        from evolution.core.constraints import ConstraintValidator
        from evolution.core.config import EvolutionConfig

        config = EvolutionConfig()
        validator = ConstraintValidator(config)
        results = validator.validate_all(content, "skill")

        return [
            {
                "passed": r.passed,
                "constraint": r.constraint_name,
                "message": r.message,
                "details": r.details,
            }
            for r in results
        ]
    except Exception:
        pass

    # Fallback: built-in validation
    results = []
    size = len(content.encode("utf-8"))
    results.append({
        "passed": size <= 15000,
        "constraint": "size_limit",
        "message": f"{size} bytes (max 15KB)",
        "details": None,
    })
    results.append({
        "passed": bool(content.strip()),
        "constraint": "non_empty",
        "message": "Skill must contain text",
        "details": None,
    })
    results.append({
        "passed": content.strip().startswith("---"),
        "constraint": "skill_structure",
        "message": "Must start with YAML frontmatter (---)",
        "details": None,
    })
    return results

# ── WEBSOCKET for live streaming ────────────────────────────────────

@app.websocket("/ws/stream")
async def websocket_stream(ws: WebSocket):
    """Real-time evolution log streaming."""
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            await ws.send_json({"type": "pong", "echo": data})
    except WebSocketDisconnect:
        manager.disconnect(ws)

# ── Health check ───────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    from .skill_registry import get_registry
    registry = get_registry()
    all_skills = registry.get_global_skills()
    skill_count = len(all_skills)
    
    # Calcular categorías desde paths
    categories = {}
    for skill in all_skills:
        cat = 'uncategorized'
        for path in [skill.get('canonical_path', '')] + [p.get('local_path', '') for p in skill.get('providers', [])]:
            if '/skills/' in path:
                parts = path.split('/skills/')
                if len(parts) > 1:
                    sub = parts[1].split('/')[0]
                    if sub and sub not in ['.', '..']:
                        cat = sub
                        break
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "status": "ok",
        "hermes_repo": str(HERMES_REPO),
        "hermes_repo_exists": HERMES_REPO.exists(),
        "evolution_dir": str(EVOLUTION_DIR),
        "evolution_dir_exists": EVOLUTION_DIR.exists(),
        "skills_count": skill_count,
        "categories": categories,
        "python": PYTHON_BIN,
    }


# ═══════════════════════════════════════════════════════════════════════
# PROMETHEAN CYCLE ENDPOINTS — GEPA ⊕ DSPy Autonomous Evolution
# ═══════════════════════════════════════════════════════════════════════

from .promethean.models import TraceRecord, CyclePhase
from .promethean.trace_ingestion import get_ingestor
from .promethean.gepa_strategist import get_strategist
from .promethean.dspy_compiler import get_compiler
from .promethean.delta_validator import get_validator
from .promethean.skill_deployer import get_deployer
from .promethean.cycle_orchestrator import get_orchestrator


@app.post("/api/promethean/traces")
async def ingest_trace(trace: dict):
    """① PERCIBE: Ingest a standardized trace from any AI agent."""
    ingestor = get_ingestor()
    try:
        trace_obj = TraceRecord.from_json(trace)
        trace_id = ingestor.ingest(trace_obj)
        return {"status": "ingested", "trace_id": trace_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/promethean/traces/batch")
async def ingest_traces_batch(traces: list[dict]):
    """① PERCIBE: Ingest multiple traces at once."""
    ingestor = get_ingestor()
    try:
        ids = ingestor.ingest_batch(traces)
        return {"status": "ingested", "count": len(ids), "trace_ids": ids}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/promethean/traces/health")
async def get_agent_health():
    """Get health summary per agent."""
    ingestor = get_ingestor()
    return {"agents": ingestor.get_agent_health(), "total_traces": ingestor.get_trace_count()}


@app.get("/api/promethean/anomalies")
async def get_anomalies(days: int = 7, min_occurrences: int = 3):
    """① PERCIBE: Get detected anomalies from recent traces."""
    ingestor = get_ingestor()
    anomalies = ingestor.get_recent_failures(days=days, min_occurrences=min_occurrences)
    return {"anomalies": anomalies, "count": len(anomalies)}


@app.get("/api/promethean/diagnose")
async def diagnose_gaps(days: int = 7, min_occurrences: int = 3):
    """②③ DIAGNOSTICA + FORMULA: GEPA analyzes anomalies and formulates learning objectives."""
    ingestor = get_ingestor()
    strategist = get_strategist()
    anomalies = ingestor.get_recent_failures(days=days, min_occurrences=min_occurrences)
    gaps = strategist.diagnose(anomalies)
    return {"gaps": gaps, "actionable": len([g for g in gaps if g["recommended_action"] == "compile_skill"])}


@app.post("/api/promethean/cycle/start")
async def start_promethean_cycle(
    min_anomaly_occurrences: int = 3,
    anomaly_days: int = 7,
    auto_deploy: bool = False,  # Safety: default to dry-run
):
    """🔥 Run the FULL Promethean Cycle (all 7 phases).

    Set auto_deploy=true to automatically register compiled skills.
    """
    orchestrator = get_orchestrator(PYTHON_BIN)
    result = await orchestrator.run_full_cycle(
        min_anomaly_occurrences=min_anomaly_occurrences,
        anomaly_days=anomaly_days,
        auto_deploy=auto_deploy,
    )
    return result


@app.get("/api/promethean/cycle/history")
async def get_cycle_history(limit: int = 10):
    """Get recent Promethean Cycle execution history."""
    orchestrator = get_orchestrator(PYTHON_BIN)
    return {"cycles": orchestrator.get_cycle_history(limit=limit)}


@app.get("/api/promethean/status")
async def get_promethean_status():
    """Get current Promethean system status."""
    ingestor = get_ingestor()
    compiler = get_compiler(PYTHON_BIN)
    return {
        "traces_ingested": ingestor.get_trace_count(),
        "dspy_available": compiler.is_available,
        "dspy_version": compiler.dspy_version,
        "python_bin": PYTHON_BIN,
        "deployments": get_deployer().get_deployment_history(limit=5),
    }


@app.get("/api/promethean/deployments")
async def get_deployments(limit: int = 20):
    """Get auto-deployed skill history."""
    return {"deployments": get_deployer().get_deployment_history(limit=limit)}


@app.post("/api/promethean/perceive")
async def run_perceive(days: int = 7, min_occurrences: int = 3):
    """Run only the PERCIBE phase (for debugging/testing)."""
    orchestrator = get_orchestrator(PYTHON_BIN)
    return orchestrator.run_perceive(days=days, min_occ=min_occurrences)


# ═══════════════════════════════════════════════════════════════════════
# CURATOR ENDPOINTS — Skill Lifecycle Management
# ═══════════════════════════════════════════════════════════════════════

CURATOR_ENABLED = True  # Can be toggled via config in the future


@app.get("/api/curator/status")
async def curator_status():
    """Curator status overview — last run, counts, pinned."""
    if not CURATOR_ENABLED:
        return {"status": "disabled"}
    from .curator import get_status
    return get_status()


@app.get("/api/curator/skills")
async def curator_skills():
    """Full usage telemetry for all skills."""
    if not CURATOR_ENABLED:
        return {"status": "disabled"}
    from .curator import get_skills_usage
    return {"skills": get_skills_usage()}


@app.post("/api/curator/pin/{skill_name:path}")
async def curator_pin(skill_name: str):
    """Pin a skill to protect it from curator auto-transitions."""
    if not CURATOR_ENABLED:
        raise HTTPException(status_code=503, detail="Curator is disabled")
    from .curator import pin_skill
    result = pin_skill(skill_name)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.post("/api/curator/unpin/{skill_name:path}")
async def curator_unpin(skill_name: str):
    """Unpin a skill to allow curator transitions."""
    if not CURATOR_ENABLED:
        raise HTTPException(status_code=503, detail="Curator is disabled")
    from .curator import unpin_skill
    result = unpin_skill(skill_name)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.post("/api/curator/restore/{skill_name:path}")
async def curator_restore(skill_name: str):
    """Restore an archived skill back to active."""
    if not CURATOR_ENABLED:
        raise HTTPException(status_code=503, detail="Curator is disabled")
    from .curator import restore_skill
    result = restore_skill(skill_name)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.post("/api/curator/run")
async def curator_run(sync: bool = False):
    """Trigger a curator review pass."""
    if not CURATOR_ENABLED:
        raise HTTPException(status_code=503, detail="Curator is disabled")
    from .curator import run_curator_review
    result = run_curator_review(sync=sync)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@app.get("/api/curator/reports")
async def curator_reports(limit: int = 10):
    """List past curator run reports."""
    if not CURATOR_ENABLED:
        return {"status": "disabled"}
    from .curator import get_reports
    return {"reports": get_reports(limit=limit)}


@app.get("/api/curator/reports/{report_id}")
async def curator_report_detail(report_id: str):
    """Get detailed curator report for a specific run."""
    if not CURATOR_ENABLED:
        raise HTTPException(status_code=503, detail="Curator is disabled")
    from .curator import get_report_detail
    result = get_report_detail(report_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


# ── Record usage (called by other parts of the dashboard) ──────────

@app.post("/api/curator/record-use")
async def curator_record_usage(data: dict):
    """Record a skill usage/view/patch event.
    
    Body: {"skill": "skill-name", "action": "use"|"view"|"patch"}
    """
    if not CURATOR_ENABLED:
        return {"status": "disabled"}
    skill = data.get("skill", "")
    action = data.get("action", "use")
    if not skill:
        raise HTTPException(status_code=400, detail="Missing 'skill' field")
    if action not in ("use", "view", "patch"):
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
    from .curator import record_use
    return record_use(skill, action)


# ═══════════════════════════════════════════════════════════════════════
# CANONICAL RUN ENDPOINTS — Phase 4 (SQLite Storage + Cross-Agent Queries)
# ═══════════════════════════════════════════════════════════════════════

from .storage import RunStore


@app.get("/api/runs")
async def list_canonical_runs(
    agent_name: Optional[str] = None,
    outcome: Optional[str] = None,
    repo: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List canonical runs with optional filters."""
    store = RunStore()
    runs = store.list_runs(
        agent_name=agent_name,
        outcome=outcome,
        repo=repo,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    return {
        "runs": [r.to_dict() for r in runs],
        "count": len(runs),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/runs/{run_id}")
async def get_canonical_run(run_id: str):
    """Get detailed canonical run by ID."""
    store = RunStore()
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return run.to_dict()


@app.get("/api/agents")
async def get_agent_summary():
    """Get per-agent statistics: count, success_rate, avg_tokens."""
    store = RunStore()
    summary = store.get_agent_summary()
    return {"agents": summary}


@app.post("/api/runs/migrate")
async def migrate_runs_from_flat_files(
    project_path: Optional[str] = None,
    limit: int = 100,
):
    """Migrate runs from flat-file collectors into SQLite.

    Runs as background task. Idempotent: re-running does not duplicate.
    """
    from .collectors.hermes_collector import HermesCollector
    from .collectors.claude_code_collector import ClaudeCodeCollector

    store = RunStore()

    # Migrate Hermes traces
    hermes_collector = HermesCollector()
    hermes_runs = hermes_collector.load_from_disk(limit=limit)
    hermes_result = store.upsert_batch(hermes_runs)

    # Migrate Claude Code sessions
    claude_collector = ClaudeCodeCollector()
    claude_runs = claude_collector.collect_all(project_path=project_path, limit=limit)
    claude_result = store.upsert_batch(claude_runs)

    return {
        "status": "completed",
        "hermes": hermes_result,
        "claude_code": claude_result,
        "total_inserted": hermes_result.get("inserted", 0) + claude_result.get("inserted", 0),
        "total_updated": hermes_result.get("updated", 0) + claude_result.get("updated", 0),
        "total_failed": hermes_result.get("failed", 0) + claude_result.get("failed", 0),
    }


@app.post("/api/runs/{run_id}/evaluate")
async def evaluate_run(run_id: str):
    """Run evaluation engine on a canonical run. Returns list of scores."""
    from .eval.engine import EvaluationEngine

    store = RunStore()
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    engine = EvaluationEngine(store=store)
    scores = engine.evaluate(run)

    return {
        "run_id": run_id,
        "scores": [
            {
                "scorer": s.scorer,
                "score": s.score,
                "passed": s.passed,
                "details": s.details,
            }
            for s in scores
        ],
        "aggregate_score": engine.get_aggregate_score(run),
    }


@app.get("/api/runs/{run_id}/scores")
async def get_run_scores(run_id: str):
    """Get evaluation scores for a run from database."""
    store = RunStore()
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    # Retrieve eval_scores from run's eval_scores list
    return {
        "run_id": run_id,
        "scores": run.eval_scores or [],
    }


@app.post("/api/runs/compare")
async def compare_runs(baseline_run_id: str, evolved_run_id: str, threshold: float = 0.05):
    """Compare baseline and evolved runs for regression detection."""
    from .eval.engine import EvaluationEngine

    store = RunStore()
    engine = EvaluationEngine(store=store)
    result = engine.detect_regression(baseline_run_id, evolved_run_id, threshold=threshold)

    return result


@app.get("/api/skills")
async def list_skills():
    """Lista skills únicas con metadata de providers y categoría."""
    from .skill_registry import get_registry
    import traceback, datetime, pathlib
    try:
        registry = get_registry()
        skills_map = {}
        for skill in registry.get_global_skills():
            name = skill['name']
            providers = [p['name'] for p in skill['providers']]
            
            # Extraer categoría del path (canonical o local del primer provider)
            category = 'uncategorized'
            for path in [skill.get('canonical_path', '')] + [p.get('local_path', '') for p in skill['providers']]:
                if '/skills/' in path:
                    parts = path.split('/skills/')
                    if len(parts) > 1:
                        sub = parts[1].split('/')[0]
                        if sub and sub not in ['.', '..']:
                            category = sub
                            break
            
            if name not in skills_map:
                skills_map[name] = {
                    "name": name,
                    "description": skill['description'],
                    "tags": skill['tags'],
                    "is_fork": skill.get('is_fork', False),
                    "canonical_path": skill['canonical_path'],
                    "providers": providers,
                    "provider_count": len(providers),
                    "category": category,
                }
        return list(skills_map.values())
    except Exception as e:
        log_path = pathlib.Path("/tmp/list_skills_error.log")
        with open(log_path, "w") as f:
            f.write(str(datetime.datetime.now()) + "\n")
            f.write(traceback.format_exc())


# ═══════════════════════════════════════════════════════════════════════
# SKILL EVOLUTION ENDPOINTS — Optimize skills with DSPy/SDD
# ═══════════════════════════════════════════════════════════════════════

@app.post("/api/skills/{skill_name}/evolve")
async def evolve_skill_endpoint(skill_name: str, iterations: int = 3):
    """Evolve a skill using SDD optimizer. Returns metrics."""
    try:
        from .sdd_evolve import evolve_skill

        # Run evolution (blocking for now — could be background job)
        evolve_skill(skill_name=skill_name, iterations=iterations)

        # Read results from output directory
        output_dir = Path.home() / ".hermes" / "hermes-agent-self-evolution" / "output" / skill_name
        runs = sorted(output_dir.glob("*/"), reverse=True) if output_dir.exists() else []

        if not runs:
            raise HTTPException(status_code=500, detail="Evolution completed but no output found")

        latest_run = runs[0]
        metrics_file = latest_run / "sdd_analysis.json"

        if not metrics_file.exists():
            raise HTTPException(status_code=500, detail="SDD analysis not found")

        metrics = json.loads(metrics_file.read_text())
        return {
            "status": "completed",
            "skill_name": skill_name,
            "iterations": iterations,
            "metrics": metrics,
            "output_dir": str(latest_run),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Evolution failed: {str(e)}")
        raise
