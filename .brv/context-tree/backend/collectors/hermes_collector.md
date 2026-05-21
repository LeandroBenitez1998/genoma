---
title: Hermes Collector
summary: Hermes Collector implementation in backend
tags: []
related: []
keywords: []
createdAt: '2026-05-21T07:40:32.607Z'
updatedAt: '2026-05-21T07:40:32.607Z'
---
## Reason
Curate backend file collectors/hermes_collector.py

## Raw Concept
**Task:**
Document collectors/hermes_collector.py

**Flow:**
input -> process -> output

**Timestamp:** 2026-05-21

## Narrative
### Structure
Source file collectors/hermes_collector.py

### Highlights
Includes backend logic for collectors/hermes_collector.py

---


&quot;&quot;&quot;Hermes collector — converts TraceRecord to CanonicalRun schema.&quot;&quot;&quot;

import json
from pathlib import Path
from typing import Optional
from backend.promethean.models import TraceRecord, CanonicalRun
from backend.promethean.trace_ingestion import TraceIngestor, INGESTED_DIR


class HermesCollector:
    &quot;&quot;&quot;Wraps TraceIngestor to emit CanonicalRun events in canonical schema.&quot;&quot;&quot;

    VERSION = &quot;0.1.0&quot;
    AGENT_NAME = &quot;hermes&quot;

    def __init__(self):
        self.ingestor = TraceIngestor()

    def collect_from_trace(self, trace: TraceRecord) -&gt; CanonicalRun:
        &quot;&quot;&quot;Convert a single TraceRecord into a CanonicalRun.&quot;&quot;&quot;
        return trace.to_canonical()

    def collect_batch(self, traces: list[TraceRecord]) -&gt; list[CanonicalRun]:
        &quot;&quot;&quot;Convert a batch of TraceRecords into CanonicalRun events.&quot;&quot;&quot;
        return [self.collect_from_trace(t) for t in traces]

    def load_from_disk(self, limit: int = 100) -&gt; list[CanonicalRun]:
        &quot;&quot;&quot;Load all ingested traces from disk and convert to CanonicalRun.&quot;&quot;&quot;
        runs = []
        ingested_path = Path(INGESTED_DIR)

        if not ingested_path.exists():
            return runs

        # Read .json files from INGESTED_DIR, up to limit
        count = 0
        for json_file in sorted(ingested_path.glob(&quot;*.json&quot;), reverse=True):
            if count &gt;= limit:
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

    def get_run_by_id(self, run_id: str) -&gt; Optional[CanonicalRun]:
        &quot;&quot;&quot;Look up a run by trace_id (run_id in CanonicalRun schema).&quot;&quot;&quot;
        ingested_path = Path(INGESTED_DIR)

        if not ingested_path.exists():
            return None

        # Search for file matching the run_id
        for json_file in ingested_path.glob(f&quot;*{run_id}*.json&quot;):
            try:
                trace_data = json.loads(json_file.read_text())
                trace = TraceRecord.from_json(trace_data)
                if trace.trace_id == run_id:
                    return self.collect_from_trace(trace)
            except Exception:
                continue

        return None

    
