"""Claude Code collector — converts session JSONL to CanonicalRun schema."""

import json
from pathlib import Path
from typing import Optional
from backend.promethean.models import CanonicalRun, ToolCallRecord, FileTouchRecord, RunMetrics


CLAUDE_SESSIONS_DIR = Path.home() / ".claude" / "projects"


class ClaudeCodeCollector:
    """Collects and normalizes Claude Code session logs into CanonicalRun events."""

    VERSION = "0.1.0"
    AGENT_NAME = "claude-code"

    def collect_session(self, session_file: Path) -> Optional[CanonicalRun]:
        """Parse a single session JSONL file into a CanonicalRun."""
        events = self._load_events(session_file)
        if not events:
            return None

        run_id = self._extract_session_id(events)
        task_name = self._extract_task(events)
        started_at, ended_at = self._extract_timestamps(events)
        model = self._extract_model(events)
        repo = self._extract_repo(events)
        tool_calls = self._extract_tool_calls(events)
        files_touched = self._extract_files_touched(events)
        metrics = self._extract_metrics(events)
        errors = self._extract_errors(events)
        outcome = self._infer_outcome(events, errors)

        return CanonicalRun(
            run_id=run_id,
            agent_name=self.AGENT_NAME,
            collector="claude-code-session-collector",
            collector_version=self.VERSION,
            started_at=started_at,
            ended_at=ended_at,
            task_name=task_name,
            outcome=outcome,
            model=model,
            provider="anthropic",
            repo=repo,
            session_id=run_id,
            tool_calls=tool_calls,
            files_touched=files_touched,
            metrics=metrics,
            errors=errors,
            context={"cwd": self._extract_cwd(events)},
        )

    def collect_all(self, project_path: Optional[str] = None, limit: int = 50) -> list[CanonicalRun]:
        """Collect runs from all sessions under a project path or all projects."""
        runs = []

        if project_path:
            # Single project: search under that path
            search_dir = Path(project_path)
        else:
            # All projects
            search_dir = CLAUDE_SESSIONS_DIR

        if not search_dir.exists():
            return runs

        count = 0
        for session_file in sorted(search_dir.rglob("*.jsonl"), reverse=True):
            if count >= limit:
                break
            try:
                run = self.collect_session(session_file)
                if run:
                    runs.append(run)
                    count += 1
            except Exception:
                continue

        return runs

    # ── Internal extraction methods ──────────────────────────────────

    def _load_events(self, path: Path) -> list[dict]:
        """Load JSONL events from file. Returns empty list on error."""
        lines = []
        try:
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    lines.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        return lines

    def _extract_session_id(self, events: list[dict]) -> str:
        """Extract or generate session ID from events."""
        for event in events:
            if isinstance(event, dict):
                # Try attachment event first (has sessionId)
                if event.get("type") == "attachment":
                    session_id = event.get("sessionId")
                    if session_id:
                        return session_id
                # Try message with sessionId
                msg = event.get("message", {})
                if isinstance(msg, dict):
                    session_id = msg.get("sessionId")
                    if session_id:
                        return session_id
        # Fallback: generate from first timestamp
        import uuid
        return str(uuid.uuid4())[:8]

    def _extract_task(self, events: list[dict]) -> str:
        """Extract task name from first user text content."""
        for event in events:
            if not isinstance(event, dict):
                continue
            if event.get("type") == "user":
                msg = event.get("message", {})
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    if isinstance(content, str) and content.strip():
                        # Clean up command wrappers
                        text = content.strip()
                        if text.startswith("<command-message>"):
                            continue
                        return text[:500]
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                text = item.get("text", "").strip()
                                if text and not text.startswith("<command-message>"):
                                    return text[:500]
        return "unknown"

    def _extract_timestamps(self, events: list[dict]) -> tuple[str, str]:
        """Extract start and end timestamps from events."""
        timestamps = []
        for event in events:
            if isinstance(event, dict) and "timestamp" in event:
                try:
                    timestamps.append(event["timestamp"])
                except Exception:
                    pass

        if not timestamps:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            return now, now

        return timestamps[0], timestamps[-1]

    def _extract_model(self, events: list[dict]) -> Optional[str]:
        """Extract model name from assistant messages."""
        for event in events:
            if isinstance(event, dict) and event.get("type") == "assistant":
                msg = event.get("message", {})
                if isinstance(msg, dict):
                    model = msg.get("model")
                    if model:
                        return model
        return None

    def _extract_repo(self, events: list[dict]) -> Optional[str]:
        """Extract repo/branch info from attachment events."""
        for event in events:
            if isinstance(event, dict) and event.get("type") == "attachment":
                git_branch = event.get("gitBranch")
                if git_branch:
                    return git_branch
        return None

    def _extract_cwd(self, events: list[dict]) -> Optional[str]:
        """Extract current working directory."""
        for event in events:
            if isinstance(event, dict) and event.get("type") == "attachment":
                cwd = event.get("cwd")
                if cwd:
                    return cwd
        return None

    def _extract_tool_calls(self, events: list[dict]) -> list[ToolCallRecord]:
        """Extract all tool_use items from assistant messages."""
        tool_calls = []
        for event in events:
            if not isinstance(event, dict) or event.get("type") != "assistant":
                continue
            msg = event.get("message", {})
            if not isinstance(msg, dict):
                continue
            for content_item in msg.get("content", []):
                if isinstance(content_item, dict) and content_item.get("type") == "tool_use":
                    tool_calls.append(ToolCallRecord(
                        id=content_item.get("id", ""),
                        name=content_item.get("name", ""),
                        input_summary=str(content_item.get("input", ""))[:200],
                    ))
        return tool_calls

    def _extract_files_touched(self, events: list[dict]) -> list[FileTouchRecord]:
        """Extract file operations from tool_use results (simplified)."""
        files = []
        for event in events:
            if not isinstance(event, dict) or event.get("type") != "user":
                continue
            msg = event.get("message", {})
            if not isinstance(msg, dict):
                continue
            for content_item in msg.get("content", []):
                if isinstance(content_item, dict) and content_item.get("type") == "tool_result":
                    # Could parse file paths from result, but simplified for MVP
                    pass
        return files

    def _extract_metrics(self, events: list[dict]) -> RunMetrics:
        """Aggregate token usage across all assistant messages."""
        total_input = total_output = total_cache = 0
        for event in events:
            if not isinstance(event, dict) or event.get("type") != "assistant":
                continue
            msg = event.get("message", {})
            if not isinstance(msg, dict):
                continue
            usage = msg.get("usage", {})
            if isinstance(usage, dict):
                total_input += usage.get("input_tokens", 0)
                total_output += usage.get("output_tokens", 0)
                total_cache += usage.get("cache_read_input_tokens", 0)

        return RunMetrics(
            input_tokens=total_input if total_input > 0 else None,
            output_tokens=total_output if total_output > 0 else None,
            cache_tokens=total_cache if total_cache > 0 else None,
            tool_call_count=len(self._extract_tool_calls(events)),
        )

    def _extract_errors(self, events: list[dict]) -> list[dict]:
        """Extract errors from system or tool_result events."""
        errors = []
        for event in events:
            if not isinstance(event, dict):
                continue
            if event.get("type") == "system":
                error = event.get("error")
                if error:
                    errors.append({
                        "signature": error[:100],
                        "message": error,
                        "stack_excerpt": None,
                        "count": 1,
                    })
        return errors

    def _infer_outcome(self, events: list[dict], errors: list[dict]) -> str:
        """Infer success/failure/partial from events."""
        # Has system error → failure
        if errors:
            return "failure" if len(errors) > 1 else "partial"

        # Check for successful completion
        for event in events:
            if not isinstance(event, dict):
                continue
            if event.get("type") == "assistant":
                msg = event.get("message", {})
                if isinstance(msg, dict):
                    stop_reason = msg.get("stop_reason")
                    if stop_reason == "end_turn":
                        return "success"

        return "unknown"
