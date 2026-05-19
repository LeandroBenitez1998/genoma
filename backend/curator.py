"""Curator Module — Skill Lifecycle Management for Hermes Dashboard

Compatible with the upstream Hermes Agent Curator format (issue #7816):
  - ~/.hermes/skills/.usage.json — per-skill telemetry
  - ~/.hermes/logs/curator/YYYYMMDD-HHMMSS/run.json + REPORT.md — per-run reports
  - ~/.hermes/skills/.archive/ — archived skills

Operates independently so it works even if the upstream Curator isn't merged yet.
"""

import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────
USAGE_FILE = Path.home() / ".hermes" / "skills" / ".usage.json"
CURATOR_LOG_DIR = Path.home() / ".hermes" / "logs" / "curator"
SKILLS_DIR = Path.home() / ".hermes" / "skills"
ARCHIVE_DIR = SKILLS_DIR / ".archive"
BUNDLED_MANIFEST = SKILLS_DIR / ".bundled_manifest"
HUB_LOCK = SKILLS_DIR / ".hub" / "lock.json"

# ── Defaults (matching upstream) ───────────────────────────────────
STALE_AFTER_DAYS = 30
ARCHIVE_AFTER_DAYS = 90

# ── Usage telemetry ────────────────────────────────────────────────

def _load_usage() -> dict:
    """Load usage telemetry from .usage.json, return empty dict if missing."""
    if USAGE_FILE.exists():
        try:
            return json.loads(USAGE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_usage(usage: dict):
    """Save usage telemetry to .usage.json."""
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(json.dumps(usage, indent=2, default=str))


def _is_agent_created(skill_name: str) -> bool:
    """Check if a skill is agent-created (not bundled or hub-installed)."""
    # Bundled check
    if BUNDLED_MANIFEST.exists():
        bundled = BUNDLED_MANIFEST.read_text().splitlines()
        for line in bundled:
            name = line.split(":")[0].strip()
            if name == skill_name:
                return False
    # Hub-installed check
    if HUB_LOCK.exists():
        try:
            hub = json.loads(HUB_LOCK.read_text())
            if isinstance(hub, dict) and skill_name in hub:
                return False
            if isinstance(hub, list):
                for entry in hub:
                    if isinstance(entry, dict) and entry.get("name") == skill_name:
                        return False
        except (json.JSONDecodeError, OSError):
            pass
    return True


# Additional skill directories to search
EXTRA_SKILL_DIRS = [
    Path.home() / ".claude" / "skills",
    Path.home() / ".hermes" / "hermes-agent" / "skills",
]


def _skill_exists(skill_name: str) -> bool:
    """Check if a skill directory exists across all known skill locations."""
    # Check primary skills dir
    if (SKILLS_DIR / skill_name).exists():
        return True
    if (ARCHIVE_DIR / skill_name).exists():
        return True
    # Check extra dirs
    for d in EXTRA_SKILL_DIRS:
        if (d / skill_name).exists():
            return True
        # Check nested categories (e.g. ~/.claude/skills/backend-patterns/)
        if (d / skill_name / "SKILL.md").exists():
            return True
    return False


# ── Public API ──────────────────────────────────────────────────────

def get_status() -> dict:
    """Return curator status: last run, counts by state, pinned list."""
    usage = _load_usage()
    
    now = datetime.now(timezone.utc)
    
    # Compute states
    active = 0
    stale = 0
    archived = 0
    pinned = []
    lru = []  # Least recently used top 5
    
    for skill_name, data in usage.items():
        state = data.get("state", "active")
        if state == "active":
            active += 1
        elif state == "stale":
            stale += 1
        elif state == "archived":
            archived += 1
        
        if data.get("pinned"):
            pinned.append(skill_name)
    
    # LRU sort
    sorted_by_use = sorted(
        [(name, data.get("last_used_at") or data.get("last_viewed_at") or "1970-01-01T00:00:00Z",
          data.get("use_count", 0), data.get("view_count", 0))
         for name, data in usage.items() if data.get("state") != "archived"],
        key=lambda x: x[1]
    )
    lru = [{"name": s[0], "last_used": s[1], "use_count": s[2], "view_count": s[3]}
           for s in sorted_by_use[:5]]
    
    # Last run
    last_run = None
    newest_dir = None
    if CURATOR_LOG_DIR.exists():
        dirs = sorted(CURATOR_LOG_DIR.iterdir()) if CURATOR_LOG_DIR.exists() else []
        if dirs:
            newest_dir = dirs[-1].name
            try:
                run_data = json.loads((CURATOR_LOG_DIR / dirs[-1].name / "run.json").read_text())
                last_run = run_data
            except (json.JSONDecodeError, OSError, IndexError):
                last_run = {"timestamp": dirs[-1].name}
    
    return {
        "status": "ok",
        "last_run": last_run or {"timestamp": None},
        "last_run_dir": newest_dir,
        "stats": {
            "active": active,
            "stale": stale,
            "archived": archived,
            "total": active + stale + archived,
            "pinned": len(pinned),
        },
        "pinned_skills": pinned,
        "least_recently_used": lru,
    }


def get_skills_usage() -> list[dict]:
    """Return usage telemetry for all tracked skills."""
    usage = _load_usage()
    results = []
    
    for skill_name, data in usage.items():
        results.append({
            "name": skill_name,
            "state": data.get("state", "active"),
            "pinned": data.get("pinned", False),
            "use_count": data.get("use_count", 0),
            "view_count": data.get("view_count", 0),
            "patch_count": data.get("patch_count", 0),
            "last_used_at": data.get("last_used_at"),
            "last_viewed_at": data.get("last_viewed_at"),
            "last_patched_at": data.get("last_patched_at"),
            "created_at": data.get("created_at"),
            "archived_at": data.get("archived_at"),
            "agent_created": _is_agent_created(skill_name),
        })
    
    # Sort by use_count descending
    results.sort(key=lambda x: x["use_count"], reverse=True)
    return results


def record_use(skill_name: str, action: str = "use"):
    """Record a usage/view/patch event for a skill.
    
    Args:
        skill_name: Name of the skill
        action: One of "use", "view", "patch"
    """
    if not _skill_exists(skill_name):
        return {"status": "error", "message": f"Skill '{skill_name}' not found"}
    
    if not _is_agent_created(skill_name):
        return {"status": "skipped", "message": f"Skill '{skill_name}' is bundled/hub-installed"}
    
    usage = _load_usage()
    now = datetime.now(timezone.utc).isoformat()
    
    if skill_name not in usage:
        usage[skill_name] = {
            "use_count": 0,
            "view_count": 0,
            "patch_count": 0,
            "state": "active",
            "pinned": False,
            "created_at": now,
            "last_used_at": None,
            "last_viewed_at": None,
            "last_patched_at": None,
            "archived_at": None,
        }
    
    entry = usage[skill_name]
    
    if action == "use":
        entry["use_count"] = entry.get("use_count", 0) + 1
        entry["last_used_at"] = now
    elif action == "view":
        entry["view_count"] = entry.get("view_count", 0) + 1
        entry["last_viewed_at"] = now
    elif action == "patch":
        entry["patch_count"] = entry.get("patch_count", 0) + 1
        entry["last_patched_at"] = now
    
    # Reset state to active on any activity
    if entry.get("state") in ("stale",):
        entry["state"] = "active"
    
    _save_usage(usage)
    return {"status": "ok", "action": action, "skill": skill_name}


def pin_skill(skill_name: str) -> dict:
    """Pin a skill to protect it from curator auto-transitions."""
    if not _skill_exists(skill_name):
        return {"status": "error", "message": f"Skill '{skill_name}' not found"}
    
    if not _is_agent_created(skill_name):
        return {
            "status": "error",
            "message": f"Cannot pin '{skill_name}' — bundled and hub-installed skills are never touched by the curator"
        }
    
    usage = _load_usage()
    if skill_name not in usage:
        usage[skill_name] = {
            "use_count": 0, "view_count": 0, "patch_count": 0,
            "state": "active", "pinned": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used_at": None, "last_viewed_at": None,
            "last_patched_at": None, "archived_at": None,
        }
    
    usage[skill_name]["pinned"] = True
    _save_usage(usage)
    return {"status": "ok", "skill": skill_name, "pinned": True}


def unpin_skill(skill_name: str) -> dict:
    """Unpin a skill to allow curator auto-transitions."""
    usage = _load_usage()
    if skill_name in usage:
        usage[skill_name]["pinned"] = False
        _save_usage(usage)
        return {"status": "ok", "skill": skill_name, "pinned": False}
    return {"status": "error", "message": f"Skill '{skill_name}' not found in usage data"}


def restore_skill(skill_name: str) -> dict:
    """Restore an archived skill back to active."""
    archive_path = ARCHIVE_DIR / skill_name
    active_path = SKILLS_DIR / skill_name
    
    if not archive_path.exists():
        return {"status": "error", "message": f"Archived skill '{skill_name}' not found"}
    
    # Check if a bundled/hub skill shadows it
    if active_path.exists():
        return {
            "status": "error",
            "message": f"Cannot restore '{skill_name}' — a skill with that name already exists in active tree"
        }
    
    # Move back
    shutil.move(str(archive_path), str(active_path))
    
    # Update usage
    usage = _load_usage()
    if skill_name in usage:
        usage[skill_name]["state"] = "active"
        usage[skill_name]["archived_at"] = None
    _save_usage(usage)
    
    return {"status": "ok", "skill": skill_name, "restored": True}


def get_reports(limit: int = 10) -> list[dict]:
    """List past curator run reports."""
    if not CURATOR_LOG_DIR.exists():
        return []
    
    dirs = sorted(CURATOR_LOG_DIR.iterdir(), reverse=True)[:limit]
    reports = []
    
    for d in dirs:
        report_path = d / "REPORT.md"
        run_path = d / "run.json"
        report = {
            "id": d.name,
            "timestamp": d.name,
            "has_report": report_path.exists(),
            "has_run_data": run_path.exists(),
        }
        if run_path.exists():
            try:
                run_data = json.loads(run_path.read_text())
                report["summary"] = {
                    "skills_reviewed": run_data.get("skills_reviewed", 0),
                    "archived": run_data.get("archived", 0),
                    "patched": run_data.get("patched", 0),
                    "consolidated": run_data.get("consolidated", 0),
                }
            except (json.JSONDecodeError, OSError):
                pass
        reports.append(report)
    
    return reports


def get_report_detail(report_id: str) -> dict:
    """Get detailed report for a specific run."""
    report_dir = CURATOR_LOG_DIR / report_id
    if not report_dir.exists():
        return {"status": "error", "message": f"Report '{report_id}' not found"}
    
    result = {"id": report_id, "timestamp": report_id}
    
    report_path = report_dir / "REPORT.md"
    if report_path.exists():
        result["report_md"] = report_path.read_text()
    
    run_path = report_dir / "run.json"
    if run_path.exists():
        try:
            result["run_data"] = json.loads(run_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    
    return result


def run_curator_review(sync: bool = False, python_bin: str = "python3") -> dict:
    """Trigger a curator review pass.
    
    In sync mode, runs inline (blocking). In background mode, returns immediately
    and the curator runs as a subprocess.
    """
    # Check if there's curator CLI
    curator_script = Path.home() / ".hermes" / "hermes-agent" / "hermes_cli" / "curator.py"
    
    if curator_script.exists():
        # Upstream curator available
        cmd = [python_bin, str(curator_script), "run"]
        if sync:
            cmd.append("--sync")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600 if sync else 30,
            )
            return {
                "status": "ok" if result.returncode == 0 else "error",
                "message": result.stdout or result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "Curator review timed out"}
        except FileNotFoundError:
            pass  # Fall through to dashboard-native curator
    
    # Dashboard-native curator (lightweight version)
    usage = _load_usage()
    now = datetime.now(timezone.utc)
    transitions = {"stale": [], "archived": []}
    
    for skill_name, data in list(usage.items()):
        if data.get("pinned"):
            continue
        if not _is_agent_created(skill_name):
            continue
        
        state = data.get("state", "active")
        last_used = data.get("last_used_at") or data.get("last_viewed_at") or data.get("created_at")
        
        if not last_used:
            continue
        
        try:
            last_dt = datetime.fromisoformat(last_used)
        except (ValueError, TypeError):
            continue
        
        days_unused = (now - last_dt).days
        current_state = state
        
        # Determine new state
        if days_unused >= ARCHIVE_AFTER_DAYS and state != "archived":
            data["state"] = "archived"
            data["archived_at"] = now.isoformat()
            transitions["archived"].append(skill_name)
            # Actually move the directory
            src = SKILLS_DIR / skill_name
            dst = ARCHIVE_DIR / skill_name
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
        elif days_unused >= STALE_AFTER_DAYS and state not in ("stale", "archived"):
            data["state"] = "stale"
            transitions["stale"].append(skill_name)
    
    _save_usage(usage)
    
    # Write report
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_dir = CURATOR_LOG_DIR / ts
    report_dir.mkdir(parents=True, exist_ok=True)
    
    run_data = {
        "timestamp": ts,
        "skills_reviewed": len(usage),
        "stale": len(transitions["stale"]),
        "archived": len(transitions["archived"]),
        "patched": 0,
        "consolidated": 0,
        "transitions": transitions,
    }
    (report_dir / "run.json").write_text(json.dumps(run_data, indent=2))
    
    report_md = [
        f"# Curator Report — {ts}",
        "",
        f"**Skills reviewed:** {len(usage)}",
        f"**Marked stale:** {len(transitions['stale'])}",
        f"**Archived:** {len(transitions['archived'])}",
        "",
        "## Transitions",
    ]
    if transitions["stale"]:
        report_md.append("\n### → Stale")
        for s in transitions["stale"]:
            report_md.append(f"- `{s}`")
    if transitions["archived"]:
        report_md.append("\n### → Archived")
        for s in transitions["archived"]:
            report_md.append(f"- `{s}`")
    if not transitions["stale"] and not transitions["archived"]:
        report_md.append("\nNo transitions.")
    
    (report_dir / "REPORT.md").write_text("\n".join(report_md))
    
    return {
        "status": "ok",
        "report_id": ts,
        "transitions": transitions,
    }


def run_auto_check():
    """Run deterministic auto-transitions (no LLM). Called by cron."""
    return run_curator_review(sync=True)


def get_all_skills_with_usage() -> list[dict]:
    """Enrich skill registry with usage data. Merges registry + usage info."""
    usage = _load_usage()
    
    # Get basic skill list from registry
    from .skill_registry import get_registry
    registry = get_registry()
    
    results = []
    for skill in registry.get_global_skills():
        name = skill["name"]
        u = usage.get(name, {})
        results.append({
            "name": name,
            "description": skill.get("description", ""),
            "tags": skill.get("tags", []),
            "category": skill.get("canonical_path", "").split("/skills/")[-1].split("/")[0] if "/skills/" in skill.get("canonical_path", "") else "uncategorized",
            "providers": [p["name"] for p in skill.get("providers", [])],
            "agent_created": _is_agent_created(name),
            "curator": {
                "state": u.get("state", "untracked"),
                "pinned": u.get("pinned", False),
                "use_count": u.get("use_count", 0),
                "view_count": u.get("view_count", 0),
                "patch_count": u.get("patch_count", 0),
                "last_used_at": u.get("last_used_at"),
                "created_at": u.get("created_at"),
            }
        })
    
    return results
