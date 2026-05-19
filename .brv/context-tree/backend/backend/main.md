---
title: main
summary: ''
tags: []
related: []
keywords: []
createdAt: '2026-04-28T01:33:30.550Z'
updatedAt: '2026-04-28T01:33:30.550Z'
---
## Reason
Preserving complete backend/main.py from hermes-dashboard project

## Raw Concept
**Task:**
Preserve backend/main.py

**Files:**
- backend/main.py

**Timestamp:** 2026-04-28

**Patterns:**
- `class ConnectionManager` - Python class definition
- `class SkillInfo` - Python class definition
- `class EvolveRequest` - Python class definition
- `class MemoryEntry` - Python class definition
- `class RunMetrics` - Python class definition
- `class ToggleSkillRequest` - Python class definition
- `def _find_python` - Python function
- `def _normalize_metrics` - Python function
- `def _find_skill_file` - Python function
- `def _parse_skill_content` - Python function

## Narrative
### Structure
Python file with 6 classes and 4 functions

### Dependencies
Classes: ConnectionManager, SkillInfo, EvolveRequest, MemoryEntry, RunMetrics, ToggleSkillRequest

### Highlights
Source: hermes-dashboard/backend/main.py

---


&quot;&quot;&quot;Hermes Evolution Dashboard — FastAPI Backend

Bridges the Next.js frontend to the hermes-agent-self-evolution Python modules.
Exposes REST endpoints + WebSocket streaming for real-time evolution monitoring.
&quot;&quot;&quot;

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

# --- Hermes Function Calling integration ---
from typing import List, Dict, Any
import json as json_module

from .skill_registry import get_registry

from .job_tracker import tracker, EvolutionJob, JobStatus

# ── Paths ──────────────────────────────────────────────────────────
HERMES_REPO = Path(os.environ.get(&quot;HERMES_AGENT_REPO&quot;, Path.home() / &quot;.hermes&quot; / &quot;hermes-agent&quot;))

# Evolution dir: env var &gt; sibling &gt; home
_env_ev = os.environ.get(&quot;EVOLUTION_DIR&quot;, &quot;&quot;)
if _env_ev:
    EVOLUTION_DIR = Path(_env_ev)
else:
    _sibling = Path(__file__).parent.parent.parent / &quot;hermes-agent-self-evolution&quot;
    _home = Path.home() / &quot;.hermes&quot; / &quot;hermes-agent-self-evolution&quot;
    EVOLUTION_DIR = _sibling if _sibling.exists() else _home

SKILLS_DIR = HERMES_REPO / &quot;skills&quot;
MEMORY_DIR = Path.home() / &quot;.hermes&quot; / &quot;memory&quot;

# ── Skill Detector ────────────────────────────────────────────────
skill_registry = get_registry()
SESSIONS_DIR = Path.home() / &quot;.hermes&quot; / &quot;sessions&quot;

# ── Python executable ──────────────────────────────────────────────
def _find_python() -&gt; str:
    &quot;&quot;&quot;Find the best Python executable (supports evolution modules).&quot;&quot;&quot;
    # 1. Env var override
    env_py = os.environ.get(&quot;PYTHON&quot;, &quot;&quot;)
    if env_py and Path(env_py).exists():
        return env_py

    # 2. System python3.12 (where dspy is installed)
    for candidate in [&quot;/usr/bin/python3&quot;, &quot;python3.12&quot;, &quot;python3.11&quot;, &quot;python3&quot;]:
        try:
            result = subprocess.run(
                [candidate, &quot;-c&quot;, &quot;import dspy; print(&apos;ok&apos;)&quot;],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    # 3. Fallback
    return sys.executable

PYTHON_BIN = _find_python()

app = FastAPI(title=&quot;Hermes Evolution API&quot;, version=&quot;0.2.0&quot;)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[&quot;http://localhost:3001&quot;, &quot;http://localhost:3000&quot;, &quot;http://127.0.0.1:3001&quot;],
    allow_credentials=True,
    allow_methods=[&quot;*&quot;],
    allow_headers=[&quot;*&quot;],
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
    source: str = &quot;skill&quot;  # &quot;skill&quot; or &quot;description&quot;

class EvolveRequest(BaseModel):
    skill_name: str
    iterations: int = 3
    eval_source: str = &quot;synthetic&quot;
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

def _normalize_metrics(raw: dict) -&gt; dict:
    &quot;&quot;&quot;Normalize metrics.json from different versions of evolve scripts.

    Supports:
    - evolve_skill.py format: skill_name, baseline_score, evolved_score, improvement
    - evolve_now.py format: skill, original_size, evolved_size, diff_lines
    &quot;&quot;&quot;
    m = dict(raw)  # shallow copy

    # Normalize skill name key
    if &quot;skill&quot; in m and &quot;skill_name&quot; not in m:
        m[&quot;skill_name&quot;] = m[&quot;skill&quot;]

    # Normalize scores
    if &quot;baseline_score&quot; not in m:
        if &quot;original_size&quot; in m and m[&quot;original_size&quot;] &gt; 0:
            # Derive a pseudo-score from size reduction (lower = more concise = better)
            ratio = m.get(&quot;evolved_size&quot;, m[&quot;original_size&quot;]) / m[&quot;original_size&quot;]
            m[&quot;baseline_score&quot;] = 0.5  # placeholder
            m[&quot;evolved_score&quot;] = min(1.0, 0.5 + (1 - ratio) * 0.3)
            m[&quot;improvement&quot;] = m[&quot;evolved_score&quot;] - m[&quot;baseline_score&quot;]
        else:
            m[&quot;baseline_score&quot;] = 0.0
            m[&quot;evolved_score&quot;] = 0.0
            m[&quot;improvement&quot;] = 0.0

    # Normalize constraints_passed
    if &quot;constraints_passed&quot; not in m:
        m[&quot;constraints_passed&quot;] = m.get(&quot;diff_lines&quot;, 0) &gt; 0

    # Normalize elapsed
    if &quot;elapsed_seconds&quot; not in m:
        m[&quot;elapsed_seconds&quot;] = 0.0

    # Normalize iterations
    if &quot;iterations&quot; not in m:
        m[&quot;iterations&quot;] = 3

    return m

def _find_skill_file(skill_name: str) -&gt; Optional[Path]:
    &quot;&quot;&quot;Find a SKILL.md by name, searching recursively.&quot;&quot;&quot;
    if not SKILLS_DIR.exists():
        return None

    # Direct path
    direct = SKILLS_DIR / skill_name / &quot;SKILL.md&quot;
    if direct.exists():
        return direct

    # Recursive search
    for f in SKILLS_DIR.rglob(&quot;SKILL.md&quot;):
        if f.parent.name == skill_name:
            return f

    return None

def _parse_skill_content(skill_file: Path) -&gt; dict:
    &quot;&quot;&quot;Parse a skill file into frontmatter + body.&quot;&quot;&quot;
    content = skill_file.read_text(encoding=&quot;utf-8&quot;, errors=&quot;replace&quot;)
    frontmatter = {}
    body = content

    if content.startswith(&quot;---&quot;):
        try:
            import yaml
            end = content.index(&quot;---&quot;, 3)
            frontmatter = yaml.safe_load(content[3:end]) or {}
            body = content[end + 3:].strip()
        except Exception:
            pass

    return {
        &quot;frontmatter&quot;: frontmatter,
        &quot;body&quot;: body,
        &quot;raw&quot;: content,
    }

# ── SKILLS endpoints ───────────────────────────────────────────────

class ToggleSkillRequest(BaseModel):
    provider: str
    skill_name: str
    enabled: bool

@app.get(&quot;/api/skills/providers&quot;)
async def list_providers():
    &quot;&quot;&quot;Lista todos los proveedores de skills detectados con sus estadísticas&quot;&quot;&quot;
    try:
        providers = skill_registry.get_providers()
        return {&quot;status&quot;: &quot;ok&quot;, &quot;providers&quot;: providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(&quot;/api/skills/provider/{provider_name}&quot;)
async def list_provider_skills(provider_name: str):
    &quot;&quot;&quot;Lista todas las skills de un proveedor específico&quot;&quot;&quot;
    try:
        providers = skill_registry.get_providers()
        for p in providers:
            if p[&quot;name&quot;] == provider_name:
                return {&quot;status&quot;: &quot;ok&quot;, &quot;provider&quot;: p}
        raise HTTPException(status_code=404, detail=f&quot;Proveedor &apos;{provider_name}&apos; no encontrado&quot;)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(&quot;/api/skills/refresh&quot;)
async def refresh_skills():
    &quot;&quot;&quot;Fuerza un re-escaneo de skills (útil para desarrollo)&quot;&quot;&quot;
    try:
        global skill_registry
        skill_registry = get_registry().rescan()
        providers = skill_registry.get_providers()
        return {&quot;status&quot;: &quot;ok&quot;, &quot;providers&quot;: providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post(&quot;/api/skills/toggle&quot;)
async def toggle_skill(request: ToggleSkillRequest):
    &quot;&quot;&quot;Activa o desactiva una skill&quot;&quot;&quot;
    try:
        skill_registry.toggle_provider_skill(request.provider, request.skill_name, request.enabled)
        return {&quot;status&quot;: &quot;ok&quot;, &quot;enabled&quot;: request.enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete(&quot;/api/skills/global/{skill_name}&quot;)
async def delete_global_skill(skill_name: str):
    &quot;&quot;&quot;Elimina una skill GLOBALMENTE (de global_skills/ y todos los symlinks).&quot;&quot;&quot;
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
            raise HTTPException(status_code=404, detail=&quot;Skill global no encontrada o es un fork&quot;)
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
        return {&quot;status&quot;: &quot;ok&quot;, &quot;message&quot;: f&quot;Skill &apos;{skill_name}&apos; eliminada globalmente&quot;}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete(&quot;/api/skills/{provider}/{skill_name}&quot;)
async def delete_skill(provider: str, skill_name: str):
    &quot;&quot;&quot;Elimina una skill de un provider específico (desenlaza, pero preserva la skill global).&quot;&quot;&quot;
    try:
        registry = get_registry()
        key = f&quot;{provider}.{skill_name}&quot;
        if key not in registry.provider_index:
            raise HTTPException(status_code=404, detail=&quot;Skill no encontrada para ese provider&quot;)
        
        gid = registry.provider_index[key]
        if gid not in registry.global_skills:
            del registry.provider_index[key]
            registry.save()
            return {&quot;status&quot;: &quot;ok&quot;, &quot;message&quot;: f&quot;Enlace eliminado (skill global no existía)&quot;}
        
        skill = registry.global_skills[gid]
        skill.providers = [p for p in skill.providers if p[&apos;name&apos;] != provider]
        del registry.provider_index[key]
        registry.save()
        return {&quot;status&quot;: &quot;ok&quot;, &quot;message&quot;: f&quot;Skill &apos;{skill_name}&apos; desenlazada de &apos;{provider}&apos;&quot;}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(&quot;/api/skills/{skill_name}&quot;)
async def get_skill(skill_name: str):
    &quot;&quot;&quot;Get full skill content + metadata.&quot;&quot;&quot;
    skill_file = _find_skill_file(skill_name)
    if not skill_file:
        raise HTTPException(404, f&quot;Skill &apos;{skill_name}&apos; not found&quot;)

    parsed = _parse_skill_content(skill_file)
    return {
        &quot;name&quot;: skill_name,
        &quot;path&quot;: str(skill_file.relative_to(HERMES_REPO)),
        &quot;frontmatter&quot;: parsed[&quot;frontmatter&quot;],
        &quot;body&quot;: parsed[&quot;body&quot;],
        &quot;raw&quot;: parsed[&quot;raw&quot;],
        &quot;size&quot;: len(parsed[&quot;raw&quot;]),
    }

@app.get(&quot;/api/evolution/runs&quot;)
async def list_evolution_runs():
    &quot;&quot;&quot;List all evolution runs — from metrics.json AND job tracker.&quot;&quot;&quot;
    output_dir = EVOLUTION_DIR / &quot;output&quot;
    all_runs = []
    seen_skills = set()

    # 1. From metrics.json files (successful runs)
    if output_dir.exists():
        for skill_dir in output_dir.iterdir():
            if skill_dir.is_dir() and skill_dir.name != &quot;skills&quot;:
                for run_dir in skill_dir.iterdir():
                    mf = run_dir / &quot;metrics.json&quot;
                    if mf.exists():
                        try:
                            data = _normalize_metrics(json.loads(mf.read_text()))
                            data.setdefault(&quot;run_dir&quot;, run_dir.name)
                            all_runs.append(data)
                            seen_skills.add(skill_dir.name)
                        except Exception:
                            pass

    # 2. From job tracker (completed/failed runs without metrics.json)
    for job in tracker.get_all_jobs(limit=200):
        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            # Check if we already have metrics for this skill
            has_metrics = any(
                r.get(&quot;skill_name&quot;) == job.skill_name
                and r.get(&quot;timestamp&quot;, &quot;&quot;).replace(&quot;_&quot;, &quot;&quot;).startswith(
                    job.started_at.replace(&quot;-&quot;, &quot;&quot;).replace(&quot;:&quot;, &quot;&quot;).replace(&quot;T&quot;, &quot;&quot;)[:8]
                )
                for r in all_runs
            )
            if not has_metrics:
                all_runs.append({
                    &quot;skill_name&quot;: job.skill_name,
                    &quot;timestamp&quot;: job.started_at.replace(&quot;-&quot;, &quot;&quot;).replace(&quot;:&quot;, &quot;&quot;).replace(&quot;T&quot;, &quot;_&quot;)[:15],
                    &quot;iterations&quot;: job.iterations,
                    &quot;baseline_score&quot;: job.baseline_score or 0.0,
                    &quot;evolved_score&quot;: job.evolved_score or 0.0,
                    &quot;improvement&quot;: job.improvement or 0.0,
                    &quot;elapsed_seconds&quot;: 0.0,
                    &quot;constraints_passed&quot;: job.status == JobStatus.COMPLETED,
                    &quot;status&quot;: job.status.value,
                    &quot;error&quot;: job.error,
                })

    return sorted(all_runs, key=lambda r: r.get(&quot;timestamp&quot;, &quot;&quot;), reverse=True)

# ── EVOLUTION endpoints ────────────────────────────────────────────

@app.get(&quot;/api/skills/{skill_name}/evolution-history&quot;)
async def skill_history(skill_name: str):
    &quot;&quot;&quot;Get evolution run history for a skill.&quot;&quot;&quot;
    output_dir = EVOLUTION_DIR / &quot;output&quot; / skill_name
    runs = []

    if output_dir.exists():
        for run_dir in sorted(output_dir.iterdir(), reverse=True):
            metrics_file = run_dir / &quot;metrics.json&quot;
            if metrics_file.exists():
                try:
                    data = json.loads(metrics_file.read_text())
                    data[&quot;run_dir&quot;] = str(run_dir.name)
                    runs.append(_normalize_metrics(data))
                except Exception:
                    pass

    # Also add from job tracker
    for job in tracker.get_all_jobs(limit=50):
        if job.skill_name == skill_name and job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            has_metrics = any(r.get(&quot;timestamp&quot;, &quot;&quot;).startswith(job.started_at[:10]) for r in runs)
            if not has_metrics:
                runs.append({
                    &quot;skill_name&quot;: job.skill_name,
                    &quot;timestamp&quot;: job.started_at.replace(&quot;-&quot;, &quot;&quot;).replace(&quot;:&quot;, &quot;&quot;).replace(&quot;T&quot;, &quot;_&quot;)[:15],
                    &quot;iterations&quot;: job.iterations,
                    &quot;baseline_score&quot;: job.baseline_score or 0.0,
                    &quot;evolved_score&quot;: job.evolved_score or 0.0,
                    &quot;improvement&quot;: job.improvement or 0.0,
                    &quot;elapsed_seconds&quot;: 0.0,
                    &quot;constraints_passed&quot;: job.status == JobStatus.COMPLETED,
                    &quot;status&quot;: job.status.value,
                    &quot;error&quot;: job.error,
                })

    return runs

@app.get(&quot;/api/skills/{skill_name}/evolution/{run_dir}/diff&quot;)
async def skill_diff(skill_name: str, run_dir: str):
    &quot;&quot;&quot;Get baseline vs evolved skill content for a specific run.&quot;&quot;&quot;
    run_path = EVOLUTION_DIR / &quot;output&quot; / skill_name / run_dir
    if not run_path.exists():
        raise HTTPException(404, f&quot;Run &apos;{run_dir}&apos; not found for skill &apos;{skill_name}&apos;&quot;)

    baseline_file = run_path / &quot;baseline_skill.md&quot;
    evolved_file = run_path / &quot;evolved_skill.md&quot;
    metrics_file = run_path / &quot;metrics.json&quot;

    result = {
        &quot;skill_name&quot;: skill_name,
        &quot;run_dir&quot;: run_dir,
        &quot;baseline&quot;: None,
        &quot;evolved&quot;: None,
        &quot;metrics&quot;: None,
    }

    if baseline_file.exists():
        result[&quot;baseline&quot;] = baseline_file.read_text(encoding=&quot;utf-8&quot;, errors=&quot;replace&quot;)
    if evolved_file.exists():
        result[&quot;evolved&quot;] = evolved_file.read_text(encoding=&quot;utf-8&quot;, errors=&quot;replace&quot;)
    if metrics_file.exists():
        try:
            result[&quot;metrics&quot;] = json.loads(metrics_file.read_text())
        except Exception:
            pass

    return result

@app.post(&quot;/api/evolution/start&quot;)
async def start_evolution(req: EvolveRequest):
    &quot;&quot;&quot;Start an evolution run with full job tracking.&quot;&quot;&quot;

    # Check for existing active jobs for this skill
    active = tracker.get_active_jobs()
    for job in active:
        if job.skill_name == req.skill_name:
            return {
                &quot;error&quot;: f&quot;Evolution already running for &apos;{req.skill_name}&apos;&quot;,
                &quot;job_id&quot;: job.id,
                &quot;status&quot;: job.status.value,
            }

    # Create tracked job
    job = tracker.create_job(req.skill_name, req.iterations)
    job.add_log(f&quot;Starting evolution for skill: {req.skill_name}&quot;)
    job.add_log(f&quot;Iterations: {req.iterations}, Source: {req.eval_source}&quot;)

    # Build command — use SDD evolution engine
    sdd_evolve_path = Path(__file__).parent / &quot;sdd_evolve.py&quot;
    cmd = [
        &quot;/usr/bin/python3&quot;, &quot;-u&quot;, str(sdd_evolve_path),
        &quot;--skill&quot;, req.skill_name,
        &quot;--iterations&quot;, str(req.iterations),
        &quot;--eval-source&quot;, req.eval_source,
    ]

    env = os.environ.copy()
    env[&quot;PYTHONUNBUFFERED&quot;] = &quot;1&quot;
    env[&quot;HERMES_AGENT_REPO&quot;] = str(HERMES_REPO)
    env[&quot;TERM&quot;] = &quot;dumb&quot;

    # ── Provider selection: Ollama preferred when available ───────────
    def _ollama_up() -&gt; bool:
        import urllib.request
        try:
            with urllib.request.urlopen(&quot;http://localhost:11434/v1/models&quot;, timeout=2) as r:
                return r.status == 200
        except Exception:
            return False

    _dotenv = dotenv_values(str(Path.home() / &quot;.hermes&quot; / &quot;.env&quot;))
    for key in (&quot;OLLAMA_API_BASE&quot;, &quot;SDD_OLLAMA_MODEL&quot;, &quot;SDD_EVOLVE_MODEL&quot;):
        if key in os.environ:
            env[key] = os.environ[key]
        elif _dotenv.get(key):
            env[key] = _dotenv[key]

    if _ollama_up():
        # Local Ollama is alive — use it regardless of stale cloud keys in .env
        base = env.get(&quot;OLLAMA_API_BASE&quot;, &quot;http://localhost:11434/v1&quot;)
        if not base.rstrip(&quot;/&quot;).endswith(&quot;/v1&quot;):
            base = base.rstrip(&quot;/&quot;) + &quot;/v1&quot;
        env[&quot;OPENAI_BASE_URL&quot;] = base
        env[&quot;OPENAI_API_KEY&quot;] = &quot;ollama&quot;
        env.setdefault(&quot;SDD_EVOLVE_MODEL&quot;, env.get(&quot;SDD_OLLAMA_MODEL&quot;, &quot;gemma4:31b-cloud&quot;))
        job.add_log(&quot;Provider: Ollama local (gemma4:31b-cloud)&quot;)
    else:
        # Forward cloud keys only when Ollama is NOT available
        for key in (&quot;OPENROUTER_API_KEY&quot;, &quot;NOUS_API_KEY&quot;, &quot;ANTHROPIC_API_KEY&quot;, &quot;OPENAI_API_KEY&quot;):
            if key in os.environ:
                env[key] = os.environ[key]
            elif _dotenv.get(key):
                env[key] = _dotenv[key]
        env.setdefault(&quot;OPENAI_BASE_URL&quot;, &quot;https://openrouter.ai/api/v1&quot;)

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
        job.error = f&quot;Failed to start process: {e}&quot;
        job.completed_at = datetime.now().isoformat()
        job.save_log()
        return {&quot;error&quot;: job.error, &quot;job_id&quot;: job.id}

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
                text = line.decode(&quot;utf-8&quot;, errors=&quot;replace&quot;).strip()

                if text:
                    # Parse line for structured updates
                    tracker.parse_line(job, text)

                    # Broadcast to WebSocket clients
                    await manager.broadcast({
                        &quot;type&quot;: &quot;evolution_log&quot;,
                        &quot;job_id&quot;: job.id,
                        &quot;skill&quot;: req.skill_name,
                        &quot;status&quot;: job.status.value,
                        &quot;progress&quot;: job.progress,
                        &quot;iteration&quot;: job.current_iteration,
                        &quot;total_iterations&quot;: job.iterations,
                        &quot;message&quot;: text,
                        &quot;timestamp&quot;: datetime.now().isoformat(),
                    })

            # Process ended
            await process.wait()
            if job.status not in (JobStatus.COMPLETED, JobStatus.FAILED):
                if process.returncode == 0:
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now().isoformat()
                    job.add_log(&quot;Process completed successfully&quot;)
                else:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now().isoformat()
                    job.error = f&quot;Process exited with code {process.returncode}&quot;
                    job.add_log(f&quot;Process failed: {job.error}&quot;)

            # Try to load final metrics from output
            output_dir = EVOLUTION_DIR / &quot;output&quot; / req.skill_name
            if output_dir.exists():
                latest_run = max(
                    [d for d in output_dir.iterdir() if d.is_dir()],
                    key=lambda d: d.stat().st_mtime,
                    default=None,
                )
                if latest_run:
                    mf = latest_run / &quot;metrics.json&quot;
                    if mf.exists():
                        try:
                            metrics = json.loads(mf.read_text())
                            job.baseline_score = metrics.get(&quot;baseline_score&quot;)
                            job.evolved_score = metrics.get(&quot;evolved_score&quot;)
                            job.improvement = metrics.get(&quot;improvement&quot;)
                        except Exception:
                            pass

            job.save_log()
            tracker.cleanup_process(job.id)

            # Broadcast completion
            await manager.broadcast({
                &quot;type&quot;: &quot;evolution_complete&quot;,
                &quot;job_id&quot;: job.id,
                &quot;skill&quot;: req.skill_name,
                &quot;status&quot;: job.status.value,
                &quot;baseline_score&quot;: job.baseline_score,
                &quot;evolved_score&quot;: job.evolved_score,
                &quot;improvement&quot;: job.improvement,
                &quot;timestamp&quot;: datetime.now().isoformat(),
            })

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now().isoformat()
            job.save_log()
            tracker.cleanup_process(job.id)

    asyncio.create_task(stream_output())

    return {
        &quot;job_id&quot;: job.id,
        &quot;skill&quot;: req.skill_name,
        &quot;status&quot;: job.status.value,
        &quot;iterations&quot;: req.iterations,
        &quot;pid&quot;: process.pid,
    }

# ── Job tracking endpoints ────────────────────────────────────────────

@app.get(&quot;/api/jobs&quot;)
async def list_jobs(active_only: bool = False, limit: int = 50):
    &quot;&quot;&quot;List evolution jobs.&quot;&quot;&quot;
    if active_only:
        jobs = tracker.get_active_jobs()
    else:
        jobs = tracker.get_all_jobs(limit)
    return [j.to_dict() for j in jobs]

@app.get(&quot;/api/jobs/{job_id}&quot;)
async def get_job(job_id: str):
    &quot;&quot;&quot;Get detailed job status including logs.&quot;&quot;&quot;
    job = tracker.get_job(job_id)
    if not job:
        raise HTTPException(404, f&quot;Job &apos;{job_id}&apos; not found&quot;)
    return job.to_dict()

@app.get(&quot;/api/jobs/{job_id}/logs&quot;)
async def get_job_logs(job_id: str, since: int = 0):
    &quot;&quot;&quot;Get job logs (optionally only lines after index `since`).&quot;&quot;&quot;
    job = tracker.get_job(job_id)
    if not job:
        raise HTTPException(404, f&quot;Job &apos;{job_id}&apos; not found&quot;)
    return {
        &quot;job_id&quot;: job_id,
        &quot;total_lines&quot;: len(job.logs),
        &quot;logs&quot;: job.logs[since:],
        &quot;status&quot;: job.status.value,
        &quot;progress&quot;: job.progress,
    }

@app.delete(&quot;/api/jobs/{job_id}&quot;)
async def cancel_job(job_id: str):
    &quot;&quot;&quot;Cancel a running evolution job.&quot;&quot;&quot;
    job = tracker.get_job(job_id)
    if not job:
        raise HTTPException(404, f&quot;Job &apos;{job_id}&apos; not found&quot;)

    process = tracker.get_process(job_id)
    if process:
        try:
            process.terminate()
            await process.wait()
        except Exception:
            pass
        tracker.cleanup_process(job_id)

    job.status = JobStatus.FAILED
    job.error = &quot;Cancelled by user&quot;
    job.completed_at = datetime.now().isoformat()
    job.save_log()

    await manager.broadcast({
        &quot;type&quot;: &quot;evolution_cancelled&quot;,
        &quot;job_id&quot;: job_id,
        &quot;skill&quot;: job.skill_name,
    })

    return {&quot;status&quot;: &quot;cancelled&quot;, &quot;job_id&quot;: job_id}

@app.get(&quot;/api/evolution/{skill_name}/output/{run_id}&quot;)
async def get_run_output(skill_name: str, run_id: str):
    &quot;&quot;&quot;Get evolved vs baseline skill diff for a specific run.&quot;&quot;&quot;
    run_dir = EVOLUTION_DIR / &quot;output&quot; / skill_name / run_id

    if not run_dir.exists():
        raise HTTPException(404, &quot;Run not found&quot;)

    result = {}

    for f in [&quot;evolved_skill.md&quot;, &quot;baseline_skill.md&quot;, &quot;evolved_FAILED.md&quot;]:
        fp = run_dir / f
        if fp.exists():
            result[f.replace(&quot;.md&quot;, &quot;&quot;)] = fp.read_text(encoding=&quot;utf-8&quot;, errors=&quot;replace&quot;)

    metrics_file = run_dir / &quot;metrics.json&quot;
    if metrics_file.exists():
        raw = json.loads(metrics_file.read_text())
        result[&quot;metrics&quot;] = _normalize_metrics(raw)

    return result

# ── DATASET endpoints ──────────────────────────────────────────────

@app.get(&quot;/api/datasets&quot;)
async def list_datasets():
    &quot;&quot;&quot;List all eval datasets.&quot;&quot;&quot;
    datasets = []

    for base in [EVOLUTION_DIR / &quot;datasets&quot;, EVOLUTION_DIR / &quot;output&quot;]:
        if not base.exists():
            continue
        for skill_dir in base.iterdir():
            if skill_dir.is_dir():
                splits = {}
                for split in [&quot;train.jsonl&quot;, &quot;val.jsonl&quot;, &quot;holdout.jsonl&quot;]:
                    fp = skill_dir / split
                    if fp.exists():
                        count = sum(1 for _ in open(fp))
                        splits[split.replace(&quot;.jsonl&quot;, &quot;&quot;)] = count
                if splits:
                    datasets.append({
                        &quot;skill&quot;: skill_dir.name,
                        &quot;path&quot;: str(skill_dir),
                        &quot;splits&quot;: splits,
                        &quot;total&quot;: sum(splits.values()),
                    })

    return datasets

@app.get(&quot;/api/datasets/{skill_name}&quot;)
async def get_dataset(skill_name: str):
    &quot;&quot;&quot;Get dataset examples for a skill.&quot;&quot;&quot;
    for base in [EVOLUTION_DIR / &quot;datasets&quot;, EVOLUTION_DIR / &quot;output&quot;]:
        dataset_dir = base / skill_name
        if dataset_dir.exists():
            result = {}
            for split in [&quot;train&quot;, &quot;val&quot;, &quot;holdout&quot;]:
                fp = dataset_dir / f&quot;{split}.jsonl&quot;
                if fp.exists():
                    examples = []
                    for line in open(fp):
                        try:
                            examples.append(json.loads(line))
                        except Exception:
                            pass
                    result[split] = examples
            return result

    raise HTTPException(404, f&quot;No dataset found for &apos;{skill_name}&apos;&quot;)

@app.get(&quot;/api/datasets/{skill_name}/sessions&quot;)
async def import_sessions(skill_name: str, source: str = &quot;all&quot;, max_examples: int = 50):
    &quot;&quot;&quot;Import and filter external sessions for dataset building.&quot;&quot;&quot;
    cmd = [
        PYTHON_BIN, &quot;-m&quot;, &quot;evolution.core.external_importers&quot;,
        &quot;--source&quot;, source,
        &quot;--skill&quot;, skill_name,
        &quot;--max-examples&quot;, str(max_examples),
        &quot;--dry-run&quot;,
    ]
    env = os.environ.copy()
    env[&quot;PYTHONPATH&quot;] = str(EVOLUTION_DIR)
    env[&quot;HERMES_AGENT_REPO&quot;] = str(HERMES_REPO)

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(EVOLUTION_DIR), env=env)

    return {
        &quot;stdout&quot;: result.stdout,
        &quot;stderr&quot;: result.stderr,
        &quot;returncode&quot;: result.returncode,
    }

# ── MEMORY endpoints ───────────────────────────────────────────────

@app.get(&quot;/api/memory&quot;)
async def list_memory():
    &quot;&quot;&quot;List all stored memories.&quot;&quot;&quot;
    memories = []

    # Check .hermes/memory directory
    if MEMORY_DIR.exists():
        for f in sorted(MEMORY_DIR.glob(&quot;*.json&quot;)):
            try:
                data = json.loads(f.read_text())
                memories.append({
                    &quot;key&quot;: f.stem,
                    &quot;data&quot;: data,
                    &quot;modified&quot;: datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
            except Exception:
                memories.append({
                    &quot;key&quot;: f.stem,
                    &quot;data&quot;: f.read_text()[:200],
                    &quot;modified&quot;: datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })

    # Also check SOUL.md memory section
    soul_path = Path.home() / &quot;.hermes&quot; / &quot;SOUL.md&quot;
    if soul_path.exists():
        content = soul_path.read_text(encoding=&quot;utf-8&quot;, errors=&quot;replace&quot;)
        if &quot;MEMORY&quot; in content:
            memories.append({
                &quot;key&quot;: &quot;SOUL_MEMORY&quot;,
                &quot;source&quot;: &quot;SOUL.md&quot;,
                &quot;size&quot;: len(content),
            })

    return memories

# ── GRAPH endpoint (vis.js format — same as graphify) ─────────────────

COMMUNITY_COLORS = [
    &quot;#4E79A7&quot;, &quot;#F28E2B&quot;, &quot;#E15759&quot;, &quot;#76B7B2&quot;, &quot;#59A14F&quot;,
    &quot;#EDC948&quot;, &quot;#B07AA1&quot;, &quot;#FF9DA7&quot;, &quot;#9C755F&quot;, &quot;#BAB0AC&quot;,
]

@app.get(&quot;/api/graph&quot;)
async def get_graph():
    &quot;&quot;&quot;Generate a vis.js knowledge graph from skills, memory, and evolution runs.

    Format matches graphify&apos;s export: nodes + edges for vis-network.
    &quot;&quot;&quot;
    nodes = {}
    edges = []
    communities = {}  # community_id -&gt; [node_ids]

    # ── 1. Skills as nodes ────────────────────────────────────────
    skill_nodes = {}
    if SKILLS_DIR.exists():
        category_map = {}  # category_dir -&gt; community_id
        cat_counter = 0

        for skill_file in sorted(SKILLS_DIR.rglob(&quot;SKILL.md&quot;)):
            skill_name = skill_file.parent.name
            category = skill_file.parent.parent.name if skill_file.parent.parent != SKILLS_DIR else &quot;root&quot;

            # Assign community by category
            if category not in category_map:
                category_map[category] = cat_counter
                communities[cat_counter] = []
                cat_counter += 1
            cid = category_map[category]

            # Read skill
            content = skill_file.read_text(encoding=&quot;utf-8&quot;, errors=&quot;replace&quot;)
            stat = skill_file.stat()
            desc = &quot;&quot;
            if content.startswith(&quot;---&quot;):
                try:
                    import yaml
                    end = content.index(&quot;---&quot;, 3)
                    fm = yaml.safe_load(content[3:end])
                    desc = (fm.get(&quot;description&quot;) or &quot;&quot;)[:80]
                except Exception:
                    pass

            node_id = f&quot;skill:{skill_name}&quot;
            deg = 0  # will update after edges
            nodes[node_id] = {
                &quot;id&quot;: node_id,
                &quot;label&quot;: skill_name,
                &quot;color&quot;: {&quot;background&quot;: COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)], &quot;border&quot;: COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)], &quot;highlight&quot;: {&quot;background&quot;: &quot;#ffffff&quot;, &quot;border&quot;: COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]}},
                &quot;size&quot;: 15,
                &quot;font&quot;: {&quot;size&quot;: 11, &quot;color&quot;: &quot;#ffffff&quot;},
                &quot;title&quot;: f&quot;{skill_name}\n{desc}&quot;,
                &quot;community&quot;: cid,
                &quot;community_name&quot;: category,
                &quot;source_file&quot;: str(skill_file.relative_to(HERMES_REPO)),
                &quot;file_type&quot;: &quot;skill&quot;,
                &quot;degree&quot;: 0,
            }
            communities[cid].append(node_id)
            skill_nodes[skill_name] = node_id

            # Edge: skill -&gt; category
            cat_node_id = f&quot;cat:{category}&quot;
            if cat_node_id not in nodes:
                nodes[cat_node_id] = {
                    &quot;id&quot;: cat_node_id,
                    &quot;label&quot;: category,
                    &quot;color&quot;: {&quot;background&quot;: &quot;#555555&quot;, &quot;border&quot;: &quot;#555555&quot;, &quot;highlight&quot;: {&quot;background&quot;: &quot;#ffffff&quot;, &quot;border&quot;: &quot;#555555&quot;}},
                    &quot;size&quot;: 22,
                    &quot;font&quot;: {&quot;size&quot;: 13, &quot;color&quot;: &quot;#ffffff&quot;},
                    &quot;title&quot;: f&quot;Category: {category}&quot;,
                    &quot;community&quot;: cid,
                    &quot;community_name&quot;: category,
                    &quot;source_file&quot;: &quot;&quot;,
                    &quot;file_type&quot;: &quot;category&quot;,
                    &quot;degree&quot;: 0,
                }
            edges.append({
                &quot;from&quot;: node_id,
                &quot;to&quot;: cat_node_id,
                &quot;label&quot;: &quot;belongs_to&quot;,
                &quot;title&quot;: &quot;belongs_to&quot;,
                &quot;dashes&quot;: False,
                &quot;width&quot;: 1,
                &quot;color&quot;: {&quot;opacity&quot;: 0.4},
                &quot;confidence&quot;: &quot;STRUCTURAL&quot;,
            })

    # ── 2. Evolution runs as edges between skill variants ─────────
    output_dir = EVOLUTION_DIR / &quot;output&quot;
    if output_dir.exists():
        for skill_dir in output_dir.iterdir():
            if skill_dir.is_dir() and skill_dir.name != &quot;skills&quot;:
                for run_dir in skill_dir.iterdir():
                    mf = run_dir / &quot;metrics.json&quot;
                    if mf.exists():
                        try:
                            data = json.loads(mf.read_text())
                            evolved_id = f&quot;evolved:{skill_dir.name}:{run_dir.name}&quot;
                            baseline_id = skill_nodes.get(skill_dir.name)

                            nodes[evolved_id] = {
                                &quot;id&quot;: evolved_id,
                                &quot;label&quot;: f&quot;{skill_dir.name} ✦&quot;,
                                &quot;color&quot;: {&quot;background&quot;: &quot;#22c55e&quot;, &quot;border&quot;: &quot;#22c55e&quot;, &quot;highlight&quot;: {&quot;background&quot;: &quot;#ffffff&quot;, &quot;border&quot;: &quot;#22c55e&quot;}},
                                &quot;size&quot;: 10 + (data.get(&quot;improvement&quot;, 0) * 100),
                                &quot;font&quot;: {&quot;size&quot;: 9, &quot;color&quot;: &quot;#a0a0a0&quot;},
                                &quot;title&quot;: f&quot;Evolved: {skill_dir.name}\nScore: {data.get(&apos;evolved_score&apos;, 0):.2f}\nImprovement: {data.get(&apos;improvement&apos;, 0)*100:.1f}%&quot;,
                                &quot;community&quot;: 0,
                                &quot;community_name&quot;: &quot;evolved&quot;,
                                &quot;source_file&quot;: str(run_dir),
                                &quot;file_type&quot;: &quot;evolution&quot;,
                                &quot;degree&quot;: 1,
                            }

                            if baseline_id:
                                edges.append({
                                    &quot;from&quot;: baseline_id,
                                    &quot;to&quot;: evolved_id,
                                    &quot;label&quot;: &quot;evolved_to&quot;,
                                    &quot;title&quot;: f&quot;+{(data.get(&apos;improvement&apos;, 0)*100):.1f}%&quot;,
                                    &quot;dashes&quot;: True,
                                    &quot;width&quot;: 2,
                                    &quot;color&quot;: {&quot;opacity&quot;: 0.8},
                                    &quot;confidence&quot;: &quot;EXTRACTED&quot;,
                                })
                        except Exception:
                            pass

    # ── 3. Memory entries as nodes ────────────────────────────────
    if MEMORY_DIR.exists():
        mem_cid = cat_counter
        communities[mem_cid] = []
        for f in sorted(MEMORY_DIR.glob(&quot;*.json&quot;)):
            try:
                mem_data = json.loads(f.read_text())
                mem_id = f&quot;memory:{f.stem}&quot;
                nodes[mem_id] = {
                    &quot;id&quot;: mem_id,
                    &quot;label&quot;: f.stem,
                    &quot;color&quot;: {&quot;background&quot;: &quot;#8b5cf6&quot;, &quot;border&quot;: &quot;#8b5cf6&quot;, &quot;highlight&quot;: {&quot;background&quot;: &quot;#ffffff&quot;, &quot;border&quot;: &quot;#8b5cf6&quot;}},
                    &quot;size&quot;: 12,
                    &quot;font&quot;: {&quot;size&quot;: 10, &quot;color&quot;: &quot;#c4b5fd&quot;},
                    &quot;title&quot;: f&quot;Memory: {f.stem}&quot;,
                    &quot;community&quot;: mem_cid,
                    &quot;community_name&quot;: &quot;memory&quot;,
                    &quot;source_file&quot;: str(f),
                    &quot;file_type&quot;: &quot;memory&quot;,
                    &quot;degree&quot;: 0,
                }
                communities[mem_cid].append(mem_id)
            except Exception:
                pass

    # ── 4. SOUL.md as hub node ────────────────────────────────────
    soul_path = Path.home() / &quot;.hermes&quot; / &quot;SOUL.md&quot;
    if soul_path.exists():
        soul_id = &quot;soul:SOUL.md&quot;
        nodes[soul_id] = {
            &quot;id&quot;: soul_id,
            &quot;label&quot;: &quot;SOUL.md&quot;,
            &quot;color&quot;: {&quot;background&quot;: &quot;#eab308&quot;, &quot;border&quot;: &quot;#eab308&quot;, &quot;highlight&quot;: {&quot;background&quot;: &quot;#ffffff&quot;, &quot;border&quot;: &quot;#eab308&quot;}},
            &quot;size&quot;: 25,
            &quot;font&quot;: {&quot;size&quot;: 13, &quot;color&quot;: &quot;#ffffff&quot;},
            &quot;title&quot;: &quot;Hermes Soul — Core identity and memory&quot;,
            &quot;community&quot;: cat_counter + 1,
            &quot;community_name&quot;: &quot;core&quot;,
            &quot;source_file&quot;: str(soul_path),
            &quot;file_type&quot;: &quot;core&quot;,
            &quot;degree&quot;: 0,
        }

    # ── Calculate degrees and node sizes ──────────────────────────
    for e in edges:
        if e[&quot;from&quot;] in nodes:
            nodes[e[&quot;from&quot;]][&quot;degree&quot;] = nodes[e[&quot;from&quot;]].get(&quot;degree&quot;, 0) + 1
        if e[&quot;to&quot;] in nodes:
            nodes[e[&quot;to&quot;]][&quot;degree&quot;] = nodes[e[&quot;to&quot;]].get(&quot;degree&quot;, 0) + 1

    max_deg = max((n.get(&quot;degree&quot;, 0) for n in nodes.values()), default=1) or 1
    for n in nodes.values():
        deg = n.get(&quot;degree&quot;, 0)
        n[&quot;size&quot;] = round(10 + 30 * (deg / max_deg), 1)
        n[&quot;font&quot;][&quot;size&quot;] = 12 if deg &gt;= max_deg * 0.15 else 0

    # ── Legend ────────────────────────────────────────────────────
    legend = []
    for cid, label in enumerate(list(category_map.keys()) if &apos;category_map&apos; in dir() else []):
        legend.append({
            &quot;cid&quot;: cid,
            &quot;color&quot;: COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)],
            &quot;label&quot;: label,
            &quot;count&quot;: len(communities.get(cid, [])),
        })

    return {
        &quot;nodes&quot;: list(nodes.values()),
        &quot;edges&quot;: edges,
        &quot;legend&quot;: legend,
        &quot;stats&quot;: {
            &quot;total_nodes&quot;: len(nodes),
            &quot;total_edges&quot;: len(edges),
            &quot;communities&quot;: len(communities),
            &quot;skills&quot;: len(skill_nodes),
        },
    }

# ── METRICS endpoints ──────────────────────────────────────────────

@app.get(&quot;/api/metrics&quot;)
async def get_metrics():
    &quot;&quot;&quot;Aggregate metrics across all evolution runs.&quot;&quot;&quot;
    output_dir = EVOLUTION_DIR / &quot;output&quot;

    all_runs = []
    if output_dir.exists():
        for skill_dir in output_dir.iterdir():
            if skill_dir.is_dir():
                for run_dir in skill_dir.iterdir():
                    mf = run_dir / &quot;metrics.json&quot;
                    if mf.exists():
                        try:
                            raw = json.loads(mf.read_text())
                            all_runs.append(_normalize_metrics(raw))
                        except Exception:
                            pass

    if not all_runs:
        return {
            &quot;total_runs&quot;: 0,
            &quot;skills_evolved&quot;: 0,
            &quot;avg_improvement&quot;: 0,
            &quot;best_improvement&quot;: 0,
            &quot;total_time_seconds&quot;: 0,
            &quot;avg_time_seconds&quot;: 0,
            &quot;success_rate&quot;: 0,
            &quot;runs&quot;: [],
        }

    improvements = [r.get(&quot;improvement&quot;, 0) for r in all_runs]
    times = [r.get(&quot;elapsed_seconds&quot;, 0) for r in all_runs]
    passed = sum(1 for r in all_runs if r.get(&quot;constraints_passed&quot;, False))
    skills = set(r.get(&quot;skill_name&quot;, &quot;unknown&quot;) for r in all_runs)

    return {
        &quot;total_runs&quot;: len(all_runs),
        &quot;skills_evolved&quot;: len(skills),
        &quot;avg_improvement&quot;: sum(improvements) / len(improvements) if improvements else 0,
        &quot;best_improvement&quot;: max(improvements) if improvements else 0,
        &quot;total_time_seconds&quot;: sum(times),
        &quot;avg_time_seconds&quot;: sum(times) / len(times) if times else 0,
        &quot;success_rate&quot;: passed / len(all_runs) if all_runs else 0,
        &quot;runs&quot;: sorted(all_runs, key=lambda r: r.get(&quot;timestamp&quot;, &quot;&quot;), reverse=True)[:20],
    }

# ── CONSTRAINTS endpoints ──────────────────────────────────────────

@app.get(&quot;/api/constraints/validate/{skill_name}&quot;)
async def validate_skill(skill_name: str):
    &quot;&quot;&quot;Validate a skill against all constraints.&quot;&quot;&quot;
    skill_file = _find_skill_file(skill_name)
    if not skill_file:
        raise HTTPException(404, f&quot;Skill &apos;{skill_name}&apos; not found&quot;)

    content = skill_file.read_text(encoding=&quot;utf-8&quot;, errors=&quot;replace&quot;)

    # Try evolution module first
    try:
        sys.path.insert(0, str(EVOLUTION_DIR))
        from evolution.core.constraints import ConstraintValidator
        from evolution.core.config import EvolutionConfig

        config = EvolutionConfig()
        validator = ConstraintValidator(config)
        results = validator.validate_all(content, &quot;skill&quot;)

        return [
            {
                &quot;passed&quot;: r.passed,
                &quot;constraint&quot;: r.constraint_name,
                &quot;message&quot;: r.message,
                &quot;details&quot;: r.details,
            }
            for r in results
        ]
    except Exception:
        pass

    # Fallback: built-in validation
    results = []
    size = len(content.encode(&quot;utf-8&quot;))
    results.append({
        &quot;passed&quot;: size &lt;= 15000,
        &quot;constraint&quot;: &quot;size_limit&quot;,
        &quot;message&quot;: f&quot;{size} bytes (max 15KB)&quot;,
        &quot;details&quot;: None,
    })
    results.append({
        &quot;passed&quot;: bool(content.strip()),
        &quot;constraint&quot;: &quot;non_empty&quot;,
        &quot;message&quot;: &quot;Skill must contain text&quot;,
        &quot;details&quot;: None,
    })
    results.append({
        &quot;passed&quot;: content.strip().startswith(&quot;---&quot;),
        &quot;constraint&quot;: &quot;skill_structure&quot;,
        &quot;message&quot;: &quot;Must start with YAML frontmatter (---)&quot;,
        &quot;details&quot;: None,
    })
    return results

# ── WEBSOCKET for live streaming ────────────────────────────────────

@app.websocket(&quot;/ws/stream&quot;)
async def websocket_stream(ws: WebSocket):
    &quot;&quot;&quot;Real-time evolution log streaming.&quot;&quot;&quot;
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            await ws.send_json({&quot;type&quot;: &quot;pong&quot;, &quot;echo&quot;: data})
    except WebSocketDisconnect:
        manager.disconnect(ws)

# ── Health check ───────────────────────────────────────────────────

@app.get(&quot;/api/health&quot;)
async def health():
    from .skill_registry import get_registry
    registry = get_registry()
    all_skills = registry.get_global_skills()
    skill_count = len(all_skills)
    
    # Calcular categorías desde paths
    categories = {}
    for skill in all_skills:
        cat = &apos;uncategorized&apos;
        for path in [skill.get(&apos;canonical_path&apos;, &apos;&apos;)] + [p.get(&apos;local_path&apos;, &apos;&apos;) for p in skill.get(&apos;providers&apos;, [])]:
            if &apos;/skills/&apos; in path:
                parts = path.split(&apos;/skills/&apos;)
                if len(parts) &gt; 1:
                    sub = parts[1].split(&apos;/&apos;)[0]
                    if sub and sub not in [&apos;.&apos;, &apos;..&apos;]:
                        cat = sub
                        break
        categories[cat] = categories.get(cat, 0) + 1

    return {
        &quot;status&quot;: &quot;ok&quot;,
        &quot;hermes_repo&quot;: str(HERMES_REPO),
        &quot;hermes_repo_exists&quot;: HERMES_REPO.exists(),
        &quot;evolution_dir&quot;: str(EVOLUTION_DIR),
        &quot;evolution_dir_exists&quot;: EVOLUTION_DIR.exists(),
        &quot;skills_count&quot;: skill_count,
        &quot;categories&quot;: categories,
        &quot;python&quot;: PYTHON_BIN,
    }

@app.get(&quot;/api/skills&quot;)
async def list_skills():
    &quot;&quot;&quot;Lista skills únicas con metadata de providers y categoría.&quot;&quot;&quot;
    from .skill_registry import get_registry
    import traceback, datetime, pathlib
    try:
        registry = get_registry()
        skills_map = {}
        for skill in registry.get_global_skills():
            name = skill[&apos;name&apos;]
            providers = [p[&apos;name&apos;] for p in skill[&apos;providers&apos;]]
            
            # Extraer categoría del path (canonical o local del primer provider)
            category = &apos;uncategorized&apos;
            for path in [skill.get(&apos;canonical_path&apos;, &apos;&apos;)] + [p.get(&apos;local_path&apos;, &apos;&apos;) for p in skill[&apos;providers&apos;]]:
                if &apos;/skills/&apos; in path:
                    parts = path.split(&apos;/skills/&apos;)
                    if len(parts) &gt; 1:
                        sub = parts[1].split(&apos;/&apos;)[0]
                        if sub and sub not in [&apos;.&apos;, &apos;..&apos;]:
                            category = sub
                            break
            
            if name not in skills_map:
                skills_map[name] = {
                    &quot;name&quot;: name,
                    &quot;description&quot;: skill[&apos;description&apos;],
                    &quot;tags&quot;: skill[&apos;tags&apos;],
                    &quot;is_fork&quot;: skill.get(&apos;is_fork&apos;, False),
                    &quot;canonical_path&quot;: skill[&apos;canonical_path&apos;],
                    &quot;providers&quot;: providers,
                    &quot;provider_count&quot;: len(providers),
                    &quot;category&quot;: category,
                }
        return list(skills_map.values())
    except Exception as e:
        log_path = pathlib.Path(&quot;/tmp/list_skills_error.log&quot;)
        with open(log_path, &quot;w&quot;) as f:
            f.write(str(datetime.datetime.now()) + &quot;\n&quot;)
            f.write(traceback.format_exc())
        raise

    
