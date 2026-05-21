---
children_hash: 9f58f3734a44ba847342635b7a5ba4dc56df5af97c53354404e8fe9f2369b1e8
compression_ratio: 0.513776337115073
condensation_order: 2
covers: [curation_context/_index.md, project_config/_index.md]
covers_token_total: 617
summary_level: d2
token_count: 317
type: summary
---
## Meta

This level aggregates repository-wide meta knowledge focused on curation workflow tracking and the canonical project setup.

### curation_context/_index.md
- Records **empty or non-actionable curation attempts** from RLM sessions.
- Main pattern: **`empty_context.md`** documents inputs that contained only placeholders such as `"."` and yielded no extractable facts.
- Used to distinguish **failed curation attempts** from genuinely processed content and to prevent reprocessing empty inputs.
- Child entries at `meta/curation_context/` provide abstract and overview variants for drill-down.

### project_config/_index.md
- Canonical entry for **repository-wide configuration and tooling**.
- Root stack includes **Next.js, TypeScript, ESLint, Tailwind, pnpm workspaces, and shadcn/ui**.
- Covers the main config files:
  - `next.config.ts`
  - `tsconfig.json`
  - `eslint.config.mjs`
  - `postcss.config.mjs`
  - `pnpm-workspace.yaml`
  - `components.json`
  - `package.json`
- Structural pattern: a **single root configuration layer** spanning build behavior, linting, workspace structure, and component tooling.
- Key flow: **config -> build -> lint -> component tooling**
- Drill-down: see **`project_configuration.md`** for the detailed canonical entry.