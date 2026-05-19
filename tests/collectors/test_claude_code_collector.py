"""Tests for ClaudeCodeCollector — Phase 3 verification."""

import json
from pathlib import Path
import pytest
from backend.promethean.models import CanonicalRun
from backend.collectors.claude_code_collector import ClaudeCodeCollector


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def collector():
    """Fixture for ClaudeCodeCollector."""
    return ClaudeCodeCollector()


@pytest.fixture
def sample_session_path():
    """Path to sample session JSONL."""
    return FIXTURES_DIR / "sample_session.jsonl"


class TestClaudeCodeCollectorBasic:
    """Basic ClaudeCodeCollector functionality tests."""

    def test_collector_instantiation(self, collector):
        """Collector should instantiate without error."""
        assert collector is not None
        assert collector.VERSION == "0.1.0"
        assert collector.AGENT_NAME == "claude-code"

    def test_collect_session_success(self, collector, sample_session_path):
        """Convert session JSONL to CanonicalRun."""
        canonical = collector.collect_session(sample_session_path)

        assert canonical is not None
        assert isinstance(canonical, CanonicalRun)
        assert canonical.agent_name == "claude-code"
        assert canonical.collector == "claude-code-session-collector"
        assert canonical.provider == "anthropic"

    def test_extract_task(self, collector, sample_session_path):
        """Task should be extracted from first user message."""
        canonical = collector.collect_session(sample_session_path)

        assert canonical.task_name == "Add dark mode toggle to React dashboard"

    def test_extract_model(self, collector, sample_session_path):
        """Model should be extracted from assistant message."""
        canonical = collector.collect_session(sample_session_path)

        assert canonical.model == "claude-opus-4-7"

    def test_extract_repo(self, collector, sample_session_path):
        """Repo/branch should be extracted from attachment event."""
        canonical = collector.collect_session(sample_session_path)

        assert canonical.repo == "feature/dark-mode"

    def test_extract_session_id(self, collector, sample_session_path):
        """Session ID should be extracted."""
        canonical = collector.collect_session(sample_session_path)

        assert canonical.session_id == "e8f7a9d3-2bc1-4f8e-9a2b-5c7e9f1d3a4b"
        assert canonical.run_id == canonical.session_id

    def test_extract_tool_calls(self, collector, sample_session_path):
        """Tool calls should be extracted from assistant messages."""
        canonical = collector.collect_session(sample_session_path)

        assert len(canonical.tool_calls) == 2
        assert canonical.tool_calls[0].name == "Read"
        assert canonical.tool_calls[1].name == "Edit"

    def test_extract_metrics(self, collector, sample_session_path):
        """Metrics should aggregate token counts."""
        canonical = collector.collect_session(sample_session_path)

        assert canonical.metrics is not None
        assert canonical.metrics.input_tokens == 1200 + 2100 + 150  # sum of usage
        assert canonical.metrics.output_tokens == 450 + 620 + 150
        assert canonical.metrics.cache_tokens == 100 + 200
        assert canonical.metrics.tool_call_count == 2

    def test_infer_outcome(self, collector, sample_session_path):
        """Outcome should be inferred as success (end_turn without errors)."""
        canonical = collector.collect_session(sample_session_path)

        assert canonical.outcome == "success"

    def test_timestamps(self, collector, sample_session_path):
        """Start and end timestamps should be extracted."""
        canonical = collector.collect_session(sample_session_path)

        assert canonical.started_at == "2026-05-19T11:22:00Z"
        assert canonical.ended_at == "2026-05-19T11:28:15Z"

    def test_cwd_in_context(self, collector, sample_session_path):
        """CWD should be in context dict."""
        canonical = collector.collect_session(sample_session_path)

        assert canonical.context.get("cwd") == "/Users/test/project"


class TestClaudeCodeCollectorRequiredFields:
    """Test that required fields are always present."""

    def test_required_fields_present(self, collector, sample_session_path):
        """All required fields must be present and non-None."""
        canonical = collector.collect_session(sample_session_path)

        required = {"run_id", "agent_name", "collector", "started_at", "task_name", "outcome"}
        for field in required:
            value = getattr(canonical, field)
            assert value is not None, f"Required field '{field}' is None"
            assert len(str(value)) > 0, f"Required field '{field}' is empty"


class TestClaudeCodeCollectorEdgeCases:
    """Edge case handling tests."""

    def test_empty_file(self, collector):
        """Empty JSONL file should return None or handle gracefully."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write("")
            path = Path(f.name)

        try:
            result = collector.collect_session(path)
            # Should return None or a run with minimal valid data
            if result:
                assert result.outcome in ["success", "failure", "partial", "unknown"]
        finally:
            path.unlink()

    def test_malformed_json_lines(self, collector):
        """Malformed JSON lines should be skipped."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"type": "user", "message": "valid"}\n')
            f.write('not valid json\n')
            f.write('{"type": "assistant", "message": {"model": "test"}}\n')
            path = Path(f.name)

        try:
            result = collector.collect_session(path)
            # Should still process the valid lines
            if result:
                assert result.model == "test"
        finally:
            path.unlink()

    def test_missing_optional_fields(self, collector):
        """Session without optional fields should still work."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"type": "user", "message": {"content": "Task"}, "timestamp": "2026-05-19T10:00:00Z"}\n')
            f.write('{"type": "assistant", "message": {"content": [{"type": "text", "text": "Response"}], "stop_reason": "end_turn"}, "timestamp": "2026-05-19T10:01:00Z"}\n')
            path = Path(f.name)

        try:
            result = collector.collect_session(path)
            assert result is not None
            assert result.outcome == "success"
            assert result.model is None  # No model in session
            assert result.repo is None   # No attachment event
        finally:
            path.unlink()
