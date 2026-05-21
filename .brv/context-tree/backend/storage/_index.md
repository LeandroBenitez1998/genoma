---
children_hash: 8dc92c00845629e849dc2275a777d8df48b266f6717a5c11585af75f3c149715
compression_ratio: 0.7463768115942029
condensation_order: 1
covers: [run_store.md]
covers_token_total: 138
summary_level: d1
token_count: 103
type: summary
---
# Storage

## Run Store
Storage layer for execution persistence and metadata. See **run_store.md** for the underlying schema and helpers.

- **Purpose:** document and manage run persistence
- **Primary file:** `backend/storage/run_store.py`
- **Core flow:** source → analysis → curated knowledge
- **Structure:** SQL schema plus run storage helpers
- **Key emphasis:** execution metadata storage and run tracking