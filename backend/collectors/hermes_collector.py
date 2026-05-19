"""Hermes collector — converts TraceRecord to CanonicalRun schema."""

import json
from pathlib import Path
from typing import Optional
from backend.promethean.models import TraceRecord, CanonicalRun
from backend.promethean.trace_ingestion import TraceIngestor, INGESTED_DIR


class HermesCollector:
    """Wraps TraceIngestor to emit CanonicalRun events in canonical schema."""

    VERSION = "0.1.0"
    AGENT_NAME = "hermes"

    def __init__(self):
        self.ingestor = TraceIngestor()

    def collect_from_trace(self, trace: TraceRecord) -> CanonicalRun:
        """Convert a single TraceRecord into a CanonicalRun."""
        return trace.to_canonical()

    def collect_batch(self, traces: list[TraceRecord]) -> list[CanonicalRun]:
        """Convert a batch of TraceRecords into CanonicalRun events."""
        return [self.collect_from_trace(t) for t in traces]

    def load_from_disk(self, limit: int = 100) -> list[CanonicalRun]:
        """Load all ingested traces from disk and convert to CanonicalRun."""
        runs = []
        ingested_path = Path(INGESTED_DIR)

        if not ingested_path.exists():
            return runs

        # Read .json files from INGESTED_DIR, up to limit
        count = 0
        for json_file in sorted(ingested_path.glob("*.json"), reverse=True):
            if count >= limit:
                break
            try:
                trace_data = json.loads(json_file.read_text())
                trace = TraceRecord.from_json(trace_data)
                runs.append(self.collect_from_trace(trace))
                count += 1
            except Exception:
                # Skip malformed traces
                continue

        return runs

    def get_run_by_id(self, run_id: str) -> Optional[CanonicalRun]:
        """Look up a run by trace_id (run_id in CanonicalRun schema)."""
        ingested_path = Path(INGESTED_DIR)

        if not ingested_path.exists():
            return None

        # Search for file matching the run_id
        for json_file in ingested_path.glob(f"*{run_id}*.json"):
            try:
                trace_data = json.loads(json_file.read_text())
                trace = TraceRecord.from_json(trace_data)
                if trace.trace_id == run_id:
                    return self.collect_from_trace(trace)
            except Exception:
                continue

        return None
