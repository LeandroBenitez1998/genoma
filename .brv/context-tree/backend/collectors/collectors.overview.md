- Describes the backend collectors package as responsible for ingesting Claude Code and Hermes sessions.
- The package is presented as a curated interface layer that turns source data into analysis and then into curated knowledge.
- Mentions collector implementations for session and trace ingestion, suggesting a pipeline-oriented architecture.
Structure / sections summary:
- Minimal document with title/summary metadata, a reason statement, raw concept block, and a short narrative section.
- Narrative emphasizes the package structure and its role in collector implementation.
Notable entities, patterns, or decisions:
- Input flow is explicitly framed as source -> analysis -> curated knowledge.
- Files referenced: backend/collectors/__init__.py.