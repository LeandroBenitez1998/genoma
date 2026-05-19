@AGENTS.md

## Skills (Auto-load based on context)

IMPORTANT: When you detect any of these contexts, IMMEDIATELY read the corresponding skill file BEFORE writing any code. These are your coding standards and workflow guides.

### Skill Discovery Paths

Skills available from multiple sources:
- **Claude Code global**: `~/.claude/skills/`
- **Plugins**: Loaded via Claude Code plugin system
- **OpenCode**: `~/.opencode/skills/`

### Framework/Library/Context Detection

| Context | Read this file |
| ------- | -------------- |
| React components, hooks, JSX, TSX files | `~/.claude/skills/react-doctor/SKILL.md` |
| Frontend UI design, mockups, layouts | `~/.claude/skills/frontend-patterns/SKILL.md` |
| Tailwind CSS classes, utilities, styles | `~/.claude/skills/tailwind/SKILL.md` |
| Next.js config, routing, Turbopack, App Router | `~/.claude/skills/nextjs-turbopack/SKILL.md` |
| TDD, unit tests, test-first workflow | `~/.claude/skills/tdd-workflow/SKILL.md` |
| PostgreSQL, SQL, database queries, migrations | `~/.opencode/skills/postgres-patterns/SKILL.md` |
| Component caching, memoization, performance | `~/.opencode/skills/cache-components/SKILL.md` |
| Bug fixes, debugging, root cause analysis | `~/.opencode/skills/fix/SKILL.md` |
| Documentation, README, docs update | `~/.opencode/skills/update-docs/SKILL.md` |
| Prompt engineering, AI prompts, LLM | `~/.opencode/skills/prompt-lookup/SKILL.md` |
| Midnight blockchain, Compact language, ZK | `~/.opencode/skills/midnight-development/SKILL.md` |
| Skill discovery, finding available skills | `~/.opencode/skills/skill-lookup/SKILL.md` |
