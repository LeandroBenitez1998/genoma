"""Tests for HermesCollector — Phase 2 verification."""

import pytest
from backend.promethean.models import TraceRecord, CanonicalRun
from backend.collectors.hermes_collector import HermesCollector


@pytest.fixture
def collector():
    """Fixture for HermesCollector."""
    return HermesCollector()


@pytest.fixture
def sample_trace():
    """Sample TraceRecord for testing."""
    return TraceRecord(
        agent="hermes",
        agent_version="2.1.143",
        timestamp="2026-05-19T14:32:00Z",
        task="Implement user authentication",
        outcome="success",
        error_signature=None,
        context={"skill_name": "auth-middleware"},
        trace_id="hermes-001"
    )


@pytest.fixture
def failed_trace():
    """TraceRecord with error."""
    return TraceRecord(
        agent="hermes",
        agent_version="2.1.143",
        timestamp="2026-05-19T14:32:00Z",
        task="Test task",
        outcome="failure",
        error_signature="TypeError: Cannot read property 'foo' of undefined",
        resolution="Rolled back changes",
        trace_id="hermes-002"
    )


class TestHermesCollectorBasic:
    """Basic HermesCollector functionality tests."""

    def test_collector_instantiation(self, collector):
        """Collector should instantiate without error."""
        assert collector is not None
        assert collector.VERSION == "0.1.0"
        assert collector.AGENT_NAME == "hermes"

    def test_collect_from_trace_success(self, collector, sample_trace):
        """Convert successful TraceRecord to CanonicalRun."""
        canonical = collector.collect_from_trace(sample_trace)

        assert isinstance(canonical, CanonicalRun)
        assert canonical.run_id == "hermes-001"
        assert canonical.agent_name == "hermes"
        assert canonical.collector == "hermes-trace-ingestor"
        assert canonical.outcome == "success"
        assert canonical.task_name == "Implement user authentication"
        assert canonical.started_at == "2026-05-19T14:32:00Z"
        assert canonical.provider == "hermes"

    def test_collect_from_trace_with_error(self, collector, failed_trace):
        """Convert failed TraceRecord with error_signature."""
        canonical = collector.collect_from_trace(failed_trace)

        assert canonical.outcome == "failure"
        assert len(canonical.errors) == 1
        assert canonical.errors[0]["signature"] == "TypeError: Cannot read property 'foo' of undefined"
        assert canonical.resolution == "Rolled back changes"

    def test_collect_from_trace_no_error(self, collector, sample_trace):
        """TraceRecord without error_signature should have empty errors list."""
        canonical = collector.collect_from_trace(sample_trace)

        assert canonical.errors == []

    def test_collect_batch(self, collector, sample_trace, failed_trace):
        """Batch conversion should work."""
        traces = [sample_trace, failed_trace]
        canonicals = collector.collect_batch(traces)

        assert len(canonicals) == 2
        assert canonicals[0].run_id == "hermes-001"
        assert canonicals[1].run_id == "hermes-002"
        assert canonicals[0].outcome == "success"
        assert canonicals[1].outcome == "failure"


class TestCanonicalRunSerialization:
    """CanonicalRun serialization tests."""

    def test_to_dict(self, collector, sample_trace):
        """CanonicalRun.to_dict() should produce valid dict."""
        canonical = collector.collect_from_trace(sample_trace)
        data = canonical.to_dict()

        assert isinstance(data, dict)
        assert data["run_id"] == "hermes-001"
        assert data["agent_name"] == "hermes"
        assert "collector" in data
        assert "started_at" in data

    def test_to_json(self, collector, sample_trace):
        """CanonicalRun.to_json() should produce valid JSON."""
        import json

        canonical = collector.collect_from_trace(sample_trace)
        json_str = canonical.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["run_id"] == "hermes-001"
        assert parsed["agent_name"] == "hermes"

    def test_from_dict_roundtrip(self, collector, sample_trace):
        """CanonicalRun should round-trip through dict."""
        original = collector.collect_from_trace(sample_trace)
        data = original.to_dict()
        restored = CanonicalRun.from_dict(data)

        assert restored.run_id == original.run_id
        assert restored.agent_name == original.agent_name
        assert restored.outcome == original.outcome
        assert restored.task_name == original.task_name

    def test_context_preservation(self, collector, sample_trace):
        """TraceRecord context should be preserved in CanonicalRun."""
        canonical = collector.collect_from_trace(sample_trace)

        assert canonical.context == {"skill_name": "auth-middleware"}

    def test_minimal_trace_conversion(self, collector):
        """Minimal TraceRecord (no optional fields) should convert."""
        minimal = TraceRecord(
            agent="hermes",
            agent_version="2.0.0",
            timestamp="2026-05-19T10:00:00Z",
            task="Minimal task",
            outcome="unknown",
            trace_id="minimal-001"
        )

        canonical = collector.collect_from_trace(minimal)

        assert canonical.run_id == "minimal-001"
        assert canonical.outcome == "unknown"
        assert canonical.errors == []
        assert canonical.context == {}
        assert canonical.resolution is None


class TestCanonicalRunRequiredFields:
    """Test that required fields are always present."""

    def test_required_fields_present(self, collector, sample_trace):
        """All required fields must be present and non-None."""
        canonical = collector.collect_from_trace(sample_trace)

        required = {"run_id", "agent_name", "collector", "started_at", "task_name", "outcome"}
        for field in required:
            value = getattr(canonical, field)
            assert value is not None, f"Required field '{field}' is None"
            assert len(str(value)) > 0, f"Required field '{field}' is empty string"
