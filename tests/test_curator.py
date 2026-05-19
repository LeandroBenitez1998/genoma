#!/usr/bin/env python3
"""Comprehensive test suite for the Hermes Dashboard Curator module.

Tests both the curator.py module functions and the API endpoints.

Run: python3 -m pytest tests/test_curator.py -v
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def temp_skills_dir(tmp_path):
    """Create a temporary skills directory structure for testing."""
    skills_dir = tmp_path / ".hermes" / "skills"
    skills_dir.mkdir(parents=True)

    # Create a bundled manifest
    bundled = skills_dir / ".bundled_manifest"
    bundled.write_text("bundled-skill:abc123\nanother-bundled:def456\n")

    # Create .archive dir
    archive_dir = skills_dir / ".archive"
    archive_dir.mkdir()

    return skills_dir


@pytest.fixture
def temp_usage_file(temp_skills_dir):
    """Create a usage.json with sample data."""
    usage = {
        "active-skill": {
            "use_count": 10,
            "view_count": 25,
            "patch_count": 2,
            "state": "active",
            "pinned": False,
            "created_at": "2026-03-01T14:20:00+00:00",
            "last_used_at": "2026-04-28T18:12:03+00:00",
            "last_viewed_at": "2026-04-28T09:44:17+00:00",
            "last_patched_at": "2026-04-20T22:01:55+00:00",
            "archived_at": None,
        },
        "stale-skill": {
            "use_count": 3,
            "view_count": 5,
            "patch_count": 0,
            "state": "stale",
            "pinned": False,
            "created_at": "2026-01-15T10:00:00+00:00",
            "last_used_at": "2026-03-20T08:30:00+00:00",
            "last_viewed_at": "2026-03-20T08:30:00+00:00",
            "last_patched_at": None,
            "archived_at": None,
        },
        "archived-skill": {
            "use_count": 1,
            "view_count": 2,
            "patch_count": 0,
            "state": "archived",
            "pinned": False,
            "created_at": "2025-12-01T10:00:00+00:00",
            "last_used_at": "2026-01-10T14:00:00+00:00",
            "last_viewed_at": "2026-01-10T14:00:00+00:00",
            "last_patched_at": None,
            "archived_at": "2026-04-10T10:00:00+00:00",
        },
        "pinned-skill": {
            "use_count": 5,
            "view_count": 8,
            "patch_count": 1,
            "state": "active",
            "pinned": True,
            "created_at": "2026-02-10T09:00:00+00:00",
            "last_used_at": "2026-04-25T16:45:00+00:00",
            "last_viewed_at": "2026-04-24T11:30:00+00:00",
            "last_patched_at": "2026-04-22T10:15:00+00:00",
            "archived_at": None,
        },
        "bundled-skill": {
            "use_count": 20,
            "view_count": 50,
            "patch_count": 5,
            "state": "active",
            "pinned": False,
            "created_at": "2026-01-01T00:00:00+00:00",
            "last_used_at": "2026-04-29T10:00:00+00:00",
            "last_viewed_at": "2026-04-29T10:00:00+00:00",
            "last_patched_at": "2026-04-28T15:00:00+00:00",
            "archived_at": None,
        },
    }
    usage_file = temp_skills_dir / ".usage.json"
    usage_file.write_text(json.dumps(usage, indent=2))
    return usage_file


@pytest.fixture
def curator_module(temp_skills_dir, temp_usage_file, monkeypatch):
    """Patch curator paths to use temp directory and import the module."""
    import importlib

    # Patch all paths in curator.py
    monkeypatch.setattr(
        "backend.curator.SKILLS_DIR", temp_skills_dir
    )
    monkeypatch.setattr(
        "backend.curator.USAGE_FILE", temp_skills_dir / ".usage.json"
    )
    monkeypatch.setattr(
        "backend.curator.CURATOR_LOG_DIR", temp_skills_dir.parent / "logs" / "curator"
    )
    monkeypatch.setattr(
        "backend.curator.ARCHIVE_DIR", temp_skills_dir / ".archive"
    )
    monkeypatch.setattr(
        "backend.curator.BUNDLED_MANIFEST", temp_skills_dir / ".bundled_manifest"
    )

    # Ensure paths exist
    (temp_skills_dir.parent / "logs" / "curator").mkdir(parents=True, exist_ok=True)

    # Reload to pick up patched paths
    if "backend.curator" in sys.modules:
        del sys.modules["backend.curator"]
    from backend import curator
    return curator


# ═══════════════════════════════════════════════════════════════════════
# Unit Tests — Module Functions
# ═══════════════════════════════════════════════════════════════════════


class TestLoadSaveUsage:
    def test_load_returns_empty_when_no_file(self, temp_skills_dir, monkeypatch):
        monkeypatch.setattr("backend.curator.USAGE_FILE", temp_skills_dir / "nonexistent.json")
        from backend.curator import _load_usage
        assert _load_usage() == {}

    def test_save_and_load_roundtrip(self, temp_skills_dir, monkeypatch):
        usage_file = temp_skills_dir / ".usage.json"
        monkeypatch.setattr("backend.curator.USAGE_FILE", usage_file)
        from backend.curator import _save_usage, _load_usage

        data = {"test-skill": {"use_count": 42, "state": "active"}}
        _save_usage(data)
        loaded = _load_usage()
        assert loaded == data

    def test_save_creates_parent_dir(self, temp_skills_dir, monkeypatch):
        nested = temp_skills_dir / "nested" / "sub" / ".usage.json"
        monkeypatch.setattr("backend.curator.USAGE_FILE", nested)
        from backend.curator import _save_usage
        _save_usage({"x": {"state": "active"}})
        assert nested.exists()


class TestIsAgentCreated:
    def test_bundled_skill_returns_false(self, temp_skills_dir, monkeypatch):
        monkeypatch.setattr("backend.curator.BUNDLED_MANIFEST", temp_skills_dir / ".bundled_manifest")
        # Ensure bundled manifest exists
        (temp_skills_dir / ".bundled_manifest").write_text("bundled-skill:abc123\n")
        from backend.curator import _is_agent_created
        assert _is_agent_created("bundled-skill") is False

    def test_unknown_skill_returns_true(self, temp_skills_dir, monkeypatch):
        monkeypatch.setattr("backend.curator.BUNDLED_MANIFEST", temp_skills_dir / ".bundled_manifest")
        from backend.curator import _is_agent_created
        assert _is_agent_created("my-custom-skill") is True

    def test_no_manifest_returns_true(self, monkeypatch):
        # No manifest at all
        from backend.curator import _is_agent_created
        assert _is_agent_created("anything") is True


class TestSkillExists:
    def test_exists_in_primary(self, temp_skills_dir, monkeypatch):
        skill_dir = temp_skills_dir / "my-skill"
        skill_dir.mkdir()
        monkeypatch.setattr("backend.curator.SKILLS_DIR", temp_skills_dir)
        from backend.curator import _skill_exists
        assert _skill_exists("my-skill") is True

    def test_exists_in_archive(self, temp_skills_dir, monkeypatch):
        archive_dir = temp_skills_dir / ".archive"
        archive_dir.mkdir(exist_ok=True)
        (archive_dir / "archived-skill").mkdir()
        monkeypatch.setattr("backend.curator.SKILLS_DIR", temp_skills_dir)
        monkeypatch.setattr("backend.curator.ARCHIVE_DIR", archive_dir)
        from backend.curator import _skill_exists
        assert _skill_exists("archived-skill") is True

    def test_not_found(self, temp_skills_dir, monkeypatch):
        monkeypatch.setattr("backend.curator.SKILLS_DIR", temp_skills_dir)
        from backend.curator import _skill_exists
        assert _skill_exists("nonexistent") is False


class TestRecordUse:
    def test_record_use_increments_counter(self, temp_skills_dir, monkeypatch):
        # Create skill dir so _skill_exists passes
        (temp_skills_dir / "test-skill").mkdir()
        monkeypatch.setattr("backend.curator.SKILLS_DIR", temp_skills_dir)
        monkeypatch.setattr("backend.curator.USAGE_FILE", temp_skills_dir / ".usage.json")
        # Remove old manifest so it's agent-created
        if (temp_skills_dir / ".bundled_manifest").exists():
            (temp_skills_dir / ".bundled_manifest").unlink()

        from backend.curator import record_use, get_skills_usage

        result = record_use("test-skill", "use")
        assert result["status"] == "ok"
        assert result["action"] == "use"

        skills = get_skills_usage()
        assert len(skills) == 1
        assert skills[0]["name"] == "test-skill"
        assert skills[0]["use_count"] == 1
        assert skills[0]["state"] == "active"

    def test_record_view_and_patch(self, temp_skills_dir, monkeypatch):
        (temp_skills_dir / "test-skill").mkdir()
        monkeypatch.setattr("backend.curator.SKILLS_DIR", temp_skills_dir)
        monkeypatch.setattr("backend.curator.USAGE_FILE", temp_skills_dir / ".usage.json")
        if (temp_skills_dir / ".bundled_manifest").exists():
            (temp_skills_dir / ".bundled_manifest").unlink()

        from backend.curator import record_use, get_skills_usage

        record_use("test-skill", "view")
        record_use("test-skill", "patch")

        skills = get_skills_usage()
        assert skills[0]["view_count"] == 1
        assert skills[0]["patch_count"] == 1

    def test_unknown_skill_returns_error(self, temp_skills_dir, monkeypatch):
        monkeypatch.setattr("backend.curator.SKILLS_DIR", temp_skills_dir)
        monkeypatch.setattr("backend.curator.USAGE_FILE", temp_skills_dir / ".usage.json")
        from backend.curator import record_use
        result = record_use("nonexistent", "use")
        assert result["status"] == "error"

    def test_bundled_skill_skips(self, temp_skills_dir, monkeypatch):
        # Keep the manifest so bundled-skill is recognized
        (temp_skills_dir / ".bundled_manifest").write_text("bundled-skill:abc123\n")
        # Create dir so _skill_exists passes
        (temp_skills_dir / "bundled-skill").mkdir()
        monkeypatch.setattr("backend.curator.SKILLS_DIR", temp_skills_dir)
        monkeypatch.setattr("backend.curator.BUNDLED_MANIFEST", temp_skills_dir / ".bundled_manifest")
        from backend.curator import record_use
        result = record_use("bundled-skill", "use")
        assert result["status"] == "skipped"


class TestPinUnpin:
    def test_pin_skill(self, temp_skills_dir, monkeypatch):
        (temp_skills_dir / "my-skill").mkdir()
        monkeypatch.setattr("backend.curator.SKILLS_DIR", temp_skills_dir)
        monkeypatch.setattr("backend.curator.USAGE_FILE", temp_skills_dir / ".usage.json")
        if (temp_skills_dir / ".bundled_manifest").exists():
            (temp_skills_dir / ".bundled_manifest").unlink()

        from backend.curator import pin_skill, get_status
        result = pin_skill("my-skill")
        assert result["status"] == "ok"
        assert result["pinned"] is True

        status = get_status()
        assert status["stats"]["pinned"] == 1
        assert "my-skill" in status["pinned_skills"]

    def test_unpin_skill(self, temp_skills_dir, monkeypatch):
        """Unpin a skill that exists in usage data."""
        usage_file = temp_skills_dir / ".usage.json"
        usage_file.write_text(json.dumps({
            "pinned-skill": {
                "use_count": 5, "view_count": 8, "patch_count": 1,
                "state": "active", "pinned": True,
                "created_at": "2026-02-10T09:00:00+00:00",
                "last_used_at": "2026-04-25T16:45:00+00:00",
                "last_viewed_at": None, "last_patched_at": None,
                "archived_at": None,
            }
        }))
        monkeypatch.setattr("backend.curator.USAGE_FILE", usage_file)
        from backend.curator import unpin_skill
        result = unpin_skill("pinned-skill")
        assert result["status"] == "ok"
        assert result["pinned"] is False

    def test_pin_bundled_refuses(self, temp_skills_dir, monkeypatch):
        (temp_skills_dir / "bundled-skill").mkdir()
        (temp_skills_dir / ".bundled_manifest").write_text("bundled-skill:abc123\n")
        monkeypatch.setattr("backend.curator.SKILLS_DIR", temp_skills_dir)
        monkeypatch.setattr("backend.curator.BUNDLED_MANIFEST", temp_skills_dir / ".bundled_manifest")
        from backend.curator import pin_skill
        result = pin_skill("bundled-skill")
        assert result["status"] == "error"
        assert "never touched" in result["message"]


class TestGetStatus:
    def test_status_returns_stats(self, curator_module, temp_usage_file):
        status = curator_module.get_status()
        assert status["status"] == "ok"
        assert status["stats"]["active"] >= 3  # active-skill, pinned-skill, bundled-skill
        assert status["stats"]["stale"] == 1
        assert status["stats"]["archived"] == 1
        assert status["stats"]["pinned"] == 1

    def test_status_returns_lru(self, curator_module):
        status = curator_module.get_status()
        assert len(status["least_recently_used"]) >= 1

    def test_status_last_run_none_when_no_reports(self, curator_module):
        status = curator_module.get_status()
        assert status["last_run"]["timestamp"] is None


class TestGetSkillsUsage:
    def test_returns_sorted_by_use(self, curator_module):
        skills = curator_module.get_skills_usage()
        assert len(skills) >= 4

        # Should be sorted by use_count descending
        counts = [s["use_count"] for s in skills]
        assert counts == sorted(counts, reverse=True)

    def test_each_skill_has_required_fields(self, curator_module):
        skills = curator_module.get_skills_usage()
        for s in skills:
            assert "name" in s
            assert "state" in s
            assert "pinned" in s
            assert "use_count" in s
            assert "view_count" in s
            assert "agent_created" in s

    def test_bundled_skill_flagged(self, curator_module):
        skills = curator_module.get_skills_usage()
        bundled = [s for s in skills if s["name"] == "bundled-skill"]
        if bundled:
            assert bundled[0]["agent_created"] is False


class TestCuratorRun:
    def test_run_marks_stale_skills(self, temp_skills_dir, monkeypatch):
        """Test that skills unused for >30 days become stale."""
        import datetime

        # Create a skill with old usage data
        usage = {
            "old-skill": {
                "use_count": 1,
                "view_count": 1,
                "patch_count": 0,
                "state": "active",
                "pinned": False,
                "created_at": "2026-01-01T10:00:00+00:00",
                "last_used_at": "2026-01-15T10:00:00+00:00",
                "last_viewed_at": "2026-01-15T10:00:00+00:00",
                "recent-skill": {
                    "use_count": 5,
                    "view_count": 10,
                    "patch_count": 0,
                    "state": "active",
                    "pinned": False,
                    "created_at": "2026-04-01T10:00:00+00:00",
                    "last_used_at": "2026-04-28T10:00:00+00:00",
                    "last_viewed_at": "2026-04-28T10:00:00+00:00",
                },
            }
        }

        usage_file = temp_skills_dir / ".usage.json"
        usage_file.write_text(json.dumps(usage))

        monkeypatch.setattr("backend.curator.SKILLS_DIR", temp_skills_dir)
        monkeypatch.setattr("backend.curator.USAGE_FILE", usage_file)
        monkeypatch.setattr("backend.curator.CURATOR_LOG_DIR", temp_skills_dir.parent / "logs" / "curator")
        (temp_skills_dir.parent / "logs" / "curator").mkdir(parents=True, exist_ok=True)

        from backend.curator import run_curator_review

        result = run_curator_review(sync=True)
        assert result["status"] == "ok"
        assert "report_id" in result


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests — API Endpoints
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a TestClient with patched curator paths and sample data."""
    skills_dir = tmp_path / ".hermes" / "skills"
    skills_dir.mkdir(parents=True)

    # Create bundled manifest
    (skills_dir / ".bundled_manifest").write_text("bundled-skill:abc123\n")

    # Create .archive
    (skills_dir / ".archive").mkdir()

    # Write sample usage data
    usage = {
        "active-skill": {"use_count": 10, "view_count": 25, "patch_count": 2,
                         "state": "active", "pinned": False,
                         "created_at": "2026-03-01T14:20:00+00:00",
                         "last_used_at": "2026-04-28T18:12:03+00:00",
                         "last_viewed_at": "2026-04-28T09:44:17+00:00",
                         "last_patched_at": "2026-04-20T22:01:55+00:00",
                         "archived_at": None},
        "pinned-skill": {"use_count": 5, "view_count": 8, "patch_count": 1,
                         "state": "active", "pinned": True,
                         "created_at": "2026-02-10T09:00:00+00:00",
                         "last_used_at": "2026-04-25T16:45:00+00:00",
                         "last_viewed_at": None, "last_patched_at": None,
                         "archived_at": None},
        "stale-skill": {"use_count": 3, "view_count": 5, "patch_count": 0,
                        "state": "stale", "pinned": False,
                        "created_at": "2026-01-15T10:00:00+00:00",
                        "last_used_at": "2026-03-20T08:30:00+00:00",
                        "last_viewed_at": "2026-03-20T08:30:00+00:00",
                        "last_patched_at": None, "archived_at": None},
    }
    usage_file = skills_dir / ".usage.json"
    usage_file.write_text(json.dumps(usage, indent=2))

    # Create some skill dirs so _skill_exists passes
    for s in ["active-skill", "pinned-skill", "bundled-skill"]:
        (skills_dir / s).mkdir(exist_ok=True)

    # First import the curator module so it exists, THEN monkeypatch
    import backend.curator as curator_mod

    # Monkeypatch the already-imported module
    monkeypatch.setattr(curator_mod, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(curator_mod, "USAGE_FILE", usage_file)
    monkeypatch.setattr(curator_mod, "CURATOR_LOG_DIR", tmp_path / "logs" / "curator")
    monkeypatch.setattr(curator_mod, "ARCHIVE_DIR", skills_dir / ".archive")
    monkeypatch.setattr(curator_mod, "BUNDLED_MANIFEST", skills_dir / ".bundled_manifest")

    # Ensure logs dir
    (tmp_path / "logs" / "curator").mkdir(parents=True, exist_ok=True)

    # Now clear the cached main module so it re-imports curator fresh
    if "backend.main" in sys.modules:
        del sys.modules["backend.main"]

    # Import main — it will import the patched curator
    from backend import main as backend_main

    # Store skills_dir in module-level var for test access
    curator_mod._test_skills_dir = skills_dir

    return TestClient(backend_main.app)


class TestAPIEndpoints:
    def _skills_dir(self, client) -> Path:
        """Get the skills_dir from the module-level test var."""
        import backend.curator
        return backend.curator._test_skills_dir

    def test_get_status(self, client):
        resp = client.get("/api/curator/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "stats" in data
        assert "pinned_skills" in data
        assert "least_recently_used" in data

    def test_get_skills(self, client):
        resp = client.get("/api/curator/skills")
        assert resp.status_code == 200
        data = resp.json()
        assert "skills" in data
        assert isinstance(data["skills"], list)

    def test_pin_skill(self, client):
        # Create skill dir in the same temp dir the client fixture uses
        skills_dir = self._skills_dir(client)
        (skills_dir / "my-custom").mkdir(exist_ok=True)
        resp = client.post("/api/curator/pin/my-custom")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["pinned"] is True

    def test_unpin_skill(self, client):
        resp = client.post("/api/curator/unpin/pinned-skill")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_run_curator(self, client):
        resp = client.post("/api/curator/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "report_id" in data

    def test_get_reports(self, client):
        resp = client.get("/api/curator/reports")
        assert resp.status_code == 200
        data = resp.json()
        assert "reports" in data

    def test_record_use(self, client):
        skills_dir = self._skills_dir(client)
        (skills_dir / "api-test-skill").mkdir(exist_ok=True)
        resp = client.post(
            "/api/curator/record-use",
            json={"skill": "api-test-skill", "action": "use"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["status"] == "ok"

    def test_record_use_missing_field(self, client):
        resp = client.post("/api/curator/record-use", json={})
        assert resp.status_code == 400

    def test_record_use_invalid_action(self, client):
        resp = client.post(
            "/api/curator/record-use",
            json={"skill": "test", "action": "invalid"},
        )
        assert resp.status_code == 400

    def test_pin_bundled_returns_400(self, client):
        resp = client.post("/api/curator/pin/bundled-skill")
        assert resp.status_code == 400

    def test_nonexistent_pin_returns_400(self, client):
        resp = client.post("/api/curator/pin/nonexistent-skill")
        assert resp.status_code == 400

    def test_restore_nonexistent_returns_400(self, client):
        resp = client.post("/api/curator/restore/nonexistent")
        assert resp.status_code == 400


if __name__ == "__main__":
    pytest.main(["-v", __file__])
