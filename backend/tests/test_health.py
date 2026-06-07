"""Smoke tests: health and auth endpoints."""
import os


class TestHealth:
    """Public health endpoint — should always be accessible."""

    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        # Expected shape from backend/main.py:health()
        assert "hermes_repo" in data
        assert "evolution_dir" in data
        assert isinstance(data["skills_count"], int)
        assert isinstance(data["categories"], dict)

    def test_health_no_auth_required(self, client):
        """Health must work without any token header."""
        resp = client.get("/api/health")
        assert resp.status_code == 200


class TestAuth:
    """Protected endpoints must reject missing/invalid token.

    NOTE: require_session_token() in core/security.py currently only checks
    for header PRESENCE — any non-empty string passes.  A production deployment
    should additionally validate against the configured _SESSION_TOKEN.
    """

    PROTECTED_POST = "/api/curator/run"

    def test_mutation_without_token_returns_401(self, client):
        """POST to a protected endpoint without X-Hermes-Session-Token."""
        resp = client.post(self.PROTECTED_POST)
        assert resp.status_code == 401

    def test_mutation_with_valid_token_succeeds(self, client):
        """POST with valid token should not return 401 (may return other codes)."""
        resp = client.post(
            self.PROTECTED_POST,
            headers={"X-Hermes-Session-Token": os.environ["GENOMA_SESSION_TOKEN"]},
        )
        assert resp.status_code != 401, "Valid token should not produce 401"

    def test_empty_token_returns_401(self, client):
        """Empty token should be rejected."""
        resp = client.post(
            self.PROTECTED_POST,
            headers={"X-Hermes-Session-Token": ""},
        )
        assert resp.status_code in (401, 422)


class TestEndpointsSmoke:
    """Quick smoke checks on public/list endpoints."""

    def test_skills_list(self, client):
        resp = client.get("/api/skills")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if data:
            assert "name" in data[0]
            assert "providers" in data[0]

    def test_metrics(self, client):
        resp = client.get("/api/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_providers_list(self, client):
        resp = client.get("/api/skills/providers")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "providers" in data
        assert isinstance(data["providers"], list)
