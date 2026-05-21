---
children_hash: 09cd2cc63fb72231d44135b7c5b856a9c1f420b2a691ea46e7385c0dac275e1a
compression_ratio: 0.5846422338568935
condensation_order: 1
covers: [project_configuration.md]
covers_token_total: 573
summary_level: d1
token_count: 335
type: summary
---
# Meta / Project Configuration

- **Project Configuration** is the canonical entry for repository-wide setup and tooling.
- It captures the root configuration stack: **Next.js**, **TypeScript**, **ESLint**, **Tailwind**, **pnpm workspaces**, and **shadcn/ui**.

## What it covers
- Build and runtime configuration via `next.config.ts`
- Type and compiler setup via `tsconfig.json`
- Linting rules via `eslint.config.mjs`
- Styling pipeline via `postcss.config.mjs`
- Workspace/package management via `pnpm-workspace.yaml`
- UI component conventions via `components.json`
- Package-level project metadata via `package.json`

## Structural pattern
- The configuration layer is organized as a **single root setup** that spans:
  - app build behavior
  - linting rules
  - workspace structure
  - component tooling
  - frontend design system support

## Key flow
- **config -> build -> lint -> component tooling**

## Key facts and relationships
- The project uses a standardized app tooling stack centered on Next.js.
- Workspace-based package management is part of the repo structure.
- shadcn/ui is integrated as the component-library convention.
- The configuration files together define the project’s build, linting, and UI component behavior.

## Drill-down
- See **project_configuration.md** for the detailed canonical knowledge entry.