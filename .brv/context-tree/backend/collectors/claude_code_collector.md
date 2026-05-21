---
title: Claude Code Collector
summary: Claude Code Collector implementation in backend
tags: []
related: []
keywords: []
createdAt: '2026-05-21T07:40:32.605Z'
updatedAt: '2026-05-21T07:40:32.605Z'
---
## Reason
Curate backend file collectors/claude_code_collector.py

## Raw Concept
**Task:**
Document collectors/claude_code_collector.py

**Flow:**
input -> process -> output

**Timestamp:** 2026-05-21

## Narrative
### Structure
Source file collectors/claude_code_collector.py

### Highlights
Includes backend logic for collectors/claude_code_collector.py

---


&quot;&quot;&quot;Claude Code collector — converts session JSONL to CanonicalRun schema.&quot;&quot;&quot;

import json
from pathlib import Path
from typing import Optional
from backend.promethean.models import CanonicalRun, ToolCallRecord, FileTouchRecord, RunMetrics


CLAUDE_SESSIONS_DIR = Path.home() / &quot;.claude&quot; / &quot;projects&quot;


class ClaudeCodeCollector:
    &quot;&quot;&quot;Collects and normalizes Claude Code session logs into CanonicalRun events.&quot;&quot;&quot;

    VERSION = &quot;0.1.0&quot;
    AGENT_NAME = &quot;claude-code&quot;

    def collect_session(self, session_file: Path) -&gt; Optional[CanonicalRun]:
        &quot;&quot;&quot;Parse a single session JSONL file into a CanonicalRun.&quot;&quot;&quot;
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
            collector=&quot;claude-code-session-collector&quot;,
            collector_version=self.VERSION,
            started_at=started_at,
            ended_at=ended_at,
            task_name=task_name,
            outcome=outcome,
            model=model,
            provider=&quot;anthropic&quot;,
            repo=repo,
            session_id=run_id,
            tool_calls=tool_calls,
            files_touched=files_touched,
            metrics=metrics,
            errors=errors,
            context={&quot;cwd&quot;: self._extract_cwd(events)},
        )

    def collect_all(self, project_path: Optional[str] = None, limit: int = 50) -&gt; list[CanonicalRun]:
        &quot;&quot;&quot;Collect runs from all sessions under a project path or all projects.&quot;&quot;&quot;
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
        for session_file in sorted(search_dir.rglob(&quot;*.jsonl&quot;), reverse=True):
            if count &gt;= limit:
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

    def _load_events(self, path: Path) -&gt; list[dict]:
        &quot;&quot;&quot;Load JSONL events from file. Returns empty list on error.&quot;&quot;&quot;
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

    def _extract_session_id(self, events: list[dict]) -&gt; str:
        &quot;&quot;&quot;Extract or generate session ID from events.&quot;&quot;&quot;
        for event in events:
            if isinstance(event, dict):
                # Try attachment event first (has sessionId)
                if event.get(&quot;type&quot;) == &quot;attachment&quot;:
                    session_id = event.get(&quot;sessionId&quot;)
                    if session_id:
                        return session_id
                # Try message with sessionId
                msg = event.get(&quot;message&quot;, {})
                if isinstance(msg, dict):
                    session_id = msg.get(&quot;sessionId&quot;)
                    if session_id:
                        return session_id
        # Fallback: generate from first timestamp
        import uuid
        return str(uuid.uuid4())[:8]

    def _extract_task(self, events: list[dict]) -&gt; str:
        &quot;&quot;&quot;Extract task name from first user text content.&quot;&quot;&quot;
        for event in events:
            if not isinstance(event, dict):
                continue
            if event.get(&quot;type&quot;) == &quot;user&quot;:
                msg = event.get(&quot;message&quot;, {})
                if isinstance(msg, dict):
                    content = msg.get(&quot;content&quot;, &quot;&quot;)
                    if isinstance(content, str) and content.strip():
                        # Clean up command wrappers
                        text = content.strip()
                        if text.startswith(&quot;&lt;command-message&gt;&quot;):
                            continue
                        return text[:500]
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get(&quot;type&quot;) == &quot;text&quot;:
                                text = item.get(&quot;text&quot;, &quot;&quot;).strip()
                                if text and not text.startswith(&quot;&lt;command-message&gt;&quot;):
                                    return text[:500]
        return &quot;unknown&quot;

    def _extract_timestamps(self, events: list[dict]) -&gt; tuple[str, str]:
        &quot;&quot;&quot;Extract start and end timestamps from events.&quot;&quot;&quot;
        timestamps = []
        for event in events:
            if isinstance(event, dict) and &quot;timestamp&quot; in event:
                try:
                    timestamps.append(event[&quot;timestamp&quot;])
                except Exception:
                    pass

        if not timestamps:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat().replace(&quot;+00:00&quot;, &quot;Z&quot;)
            return now, now

        return timestamps[0], timestamps[-1]

    def _extract_model(self, events: list[dict]) -&gt; Optional[str]:
        &quot;&quot;&quot;Extract model name from assistant messages.&quot;&quot;&quot;
        for event in events:
            if isinstance(event, dict) and event.get(&quot;type&quot;) == &quot;assistant&quot;:
                msg = event.get(&quot;message&quot;, {})
                if isinstance(msg, dict):
                    model = msg.get(&quot;model&quot;)
                    if model:
                        return model
        return None

    def _extract_repo(self, events: list[dict]) -&gt; Optional[str]:
        &quot;&quot;&quot;Extract repo/branch info from attachment events.&quot;&quot;&quot;
        for event in events:
            if isinstance(event, dict) and event.get(&quot;type&quot;) == &quot;attachment&quot;:
                git_branch = event.get(&quot;gitBranch&quot;)
                if git_branch:
                    return git_branch
        return None

    def _extract_cwd(self, events: list[dict]) -&gt; Optional[str]:
        &quot;&quot;&quot;Extract current working directory.&quot;&quot;&quot;
        for event in events:
            if isinstance(event, dict) and event.get(&quot;type&quot;) == &quot;attachment&quot;:
                cwd = event.get(&quot;cwd&quot;)
                if cwd:
                    return cwd
        return None

    def _extract_tool_calls(self, events: list[dict]) -&gt; list[ToolCallRecord]:
        &quot;&quot;&quot;Extract all tool_use items from assistant messages.&quot;&quot;&quot;
        tool_calls = []
        for event in events:
            if not isinstance(event, dict) or event.get(&quot;type&quot;) != &quot;assistant&quot;:
                continue
            msg = event.get(&quot;message&quot;, {})
            if not isinstance(msg, dict):
                continue
            for content_item in msg.get(&quot;content&quot;, []):
                if isinstance(content_item, dict) and content_item.get(&quot;type&quot;) == &quot;tool_use&quot;:
                    tool_calls.append(ToolCallRecord(
                        id=content_item.get(&quot;id&quot;, &quot;&quot;),
                        name=content_item.get(&quot;name&quot;, &quot;&quot;),
                        input_summary=str(content_item.get(&quot;input&quot;, &quot;&quot;))[:200],
                    ))
        return tool_calls

    def _extract_files_touched(self, events: list[dict]) -&gt; list[FileTouchRecord]:
        &quot;&quot;&quot;Extract file operations from tool_use results (simplified).&quot;&quot;&quot;
        files = []
        for event in events:
            if not isinstance(event, dict) or event.get(&quot;type&quot;) != &quot;user&quot;:
                continue
            msg = event.get(&quot;message&quot;, {})
            if not isinstance(msg, dict):
                continue
            for content_item in msg.get(&quot;content&quot;, []):
                if isinstance(content_item, dict) and content_item.get(&quot;type&quot;) == &quot;tool_result&quot;:
                    # Could parse file paths from result, but simplified for MVP
                    pass
        return files

    def _extract_metrics(self, events: list[dict]) -&gt; RunMetrics:
        &quot;&quot;&quot;Aggregate token usage across all assistant messages.&quot;&quot;&quot;
        total_input = total_output = total_cache = 0
        for event in events:
            if not isinstance(event, dict) or event.get(&quot;type&quot;) != &quot;assistant&quot;:
                continue
            msg = event.get(&quot;message&quot;, {})
            if not isinstance(msg, dict):
                continue
            usage = msg.get(&quot;usage&quot;, {})
            if isinstance(usage, dict):
                total_input += usage.get(&quot;input_tokens&quot;, 0)
                total_output += usage.get(&quot;output_tokens&quot;, 0)
                total_cache += usage.get(&quot;cache_read_input_tokens&quot;, 0)

        return RunMetrics(
            input_tokens=total_input if total_input &gt; 0 else None,
            output_tokens=total_output if total_output &gt; 0 else None,
            cache_tokens=total_cache if total_cache &gt; 0 else None,
            tool_call_count=len(self._extract_tool_calls(events)),
        )

    def _extract_errors(self, events: list[dict]) -&gt; list[dict]:
        &quot;&quot;&quot;Extract errors from system or tool_result events.&quot;&quot;&quot;
        errors = []
        for event in events:
            if not isinstance(event, dict):
                continue
            if event.get(&quot;type&quot;) == &quot;system&quot;:
                error = event.get(&quot;error&quot;)
                if error:
                    errors.append({
                        &quot;signature&quot;: error[:100],
                        &quot;message&quot;: error,
                        &quot;stack_excerpt&quot;: None,
                        &quot;count&quot;: 1,
                    })
        return errors

    def _infer_outcome(self, events: list[dict], errors: list[dict]) -&gt; str:
        &quot;&quot;&quot;Infer success/failure/partial from events.&quot;&quot;&quot;
        # Has system error → failure
        if errors:
            return &quot;failure&quot; if len(errors) &gt; 1 else &quot;partial&quot;

        # Check for successful completion
        for event in events:
            if not isinstance(event, dict):
                continue
            if event.get(&quot;type&quot;) == &quot;assistant&quot;:
                msg = event.get(&quot;message&quot;, {})
                if isinstance(msg, dict):
                    stop_reason = msg.get(&quot;stop_reason&quot;)
                    if stop_reason == &quot;end_turn&quot;:
                        return &quot;success&quot;

        return &quot;unknown&quot;

    
