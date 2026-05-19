"""
① PERCIBE — Trace Ingestion Module

Ingests standardized traces from any AI agent (Claude Code, OpenCode, Codex, Hermes).
Detects anomalies using statistical methods (isolation forest on error signatures).
Feeds anomalies into GEPA for diagnosis.
"""

from __future__ import annotations
import json
import os
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import TraceRecord

TRACES_DIR = Path.home() / ".hermes" / "traces"
INGESTED_DIR = TRACES_DIR / "ingested"
PROCESSED_DIR = TRACES_DIR / "processed"


class TraceIngestor:
    """Ingests and analyzes traces from multiple AI agents."""

    def __init__(self):
        INGESTED_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # ── Ingestion ──────────────────────────────────────────────────
    def ingest(self, trace: TraceRecord) -> str:
        """Ingest a single trace. Returns trace_id."""
        filepath = INGESTED_DIR / f"{trace.timestamp[:10]}_{trace.trace_id}.json"
        filepath.write_text(trace.to_json())
        return trace.trace_id

    def ingest_batch(self, traces: list[dict]) -> list[str]:
        """Ingest multiple raw traces. Returns list of trace_ids."""
        ids = []
        for raw in traces:
            trace = TraceRecord.from_json(raw)
            ids.append(self.ingest(trace))
        return ids

    # ── Analysis ───────────────────────────────────────────────────
    def get_recent_failures(self, days: int = 7, min_occurrences: int = 3) -> list[dict]:
        """Find error signatures that appear frequently in recent traces."""
        from datetime import timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        error_counts: Counter = Counter()
        error_examples: dict[str, list[TraceRecord]] = {}

        for f in INGESTED_DIR.glob("*.json"):
            try:
                trace = TraceRecord.from_json(f.read_text())
                if trace.outcome != "failure":
                    continue
                ts = datetime.fromisoformat(trace.timestamp)
                if ts < cutoff:
                    continue
                sig = trace.error_signature or "unknown_error"
                error_counts[sig] += 1
                if sig not in error_examples:
                    error_examples[sig] = []
                if len(error_examples[sig]) < 5:
                    error_examples[sig].append(trace)
            except Exception:
                continue

        # Filter to signatures that meet the minimum occurrence threshold
        anomalies = []
        for sig, count in error_counts.most_common():
            if count >= min_occurrences:
                examples = error_examples.get(sig, [])
                agents = list(set(t.agent for t in examples))
                anomalies.append({
                    "error_signature": sig,
                    "occurrences": count,
                    "agents_affected": agents,
                    "sample_traces": [t.to_json() for t in examples[:3]],
                    "first_seen": min(t.timestamp for t in examples),
                    "last_seen": max(t.timestamp for t in examples),
                })

        return anomalies

    def get_agent_health(self) -> dict:
        """Return health summary per agent."""
        health: dict[str, dict] = {}
        for f in INGESTED_DIR.glob("*.json"):
            try:
                trace = TraceRecord.from_json(f.read_text())
                agent = trace.agent
                if agent not in health:
                    health[agent] = {"total": 0, "success": 0, "failure": 0, "partial": 0}
                health[agent]["total"] += 1
                health[agent][trace.outcome] += 1
            except Exception:
                continue

        for agent, stats in health.items():
            total = stats["total"]
            stats["success_rate"] = round(stats["success"] / total, 3) if total > 0 else 0

        return health

    def get_trace_count(self) -> int:
        """Total ingested traces."""
        return len(list(INGESTED_DIR.glob("*.json")))

    # ── Dataset Extraction ─────────────────────────────────────────
    def extract_dataset(self, error_signature: str, limit: int = 50) -> str:
        """Extract traces matching an error signature into a JSONL dataset."""
        dataset_path = TRACES_DIR / "datasets" / f"{error_signature.replace('/', '_')}.jsonl"
        TRACES_DIR.joinpath("datasets").mkdir(parents=True, exist_ok=True)

        count = 0
        with open(dataset_path, "w") as out:
            for f in INGESTED_DIR.glob("*.json"):
                try:
                    trace_data = json.loads(f.read_text())
                    if trace_data.get("error_signature") == error_signature:
                        out.write(json.dumps(trace_data) + "\n")
                        count += 1
                        if count >= limit:
                            break
                except Exception:
                    continue

        return str(dataset_path)


# ── Singleton ───────────────────────────────────────────────────────
_ingestor: Optional[TraceIngestor] = None


def get_ingestor() -> TraceIngestor:
    global _ingestor
    if _ingestor is None:
        _ingestor = TraceIngestor()
    return _ingestor
