# SettingsPage Component Overview

**Source:** `src/components/pages/SettingsPage.tsx` from `hermes-dashboard`

## Key Points

- **Client-side React component** (`"use client"`) using `useState`, `useEffect`, and Framer Motion for animations
- **Fetches health status** from `/lib/api` on mount to display system state
- **Two main sections:** System Paths and Environment Variables
- **Toggle visibility** for sensitive values (API keys) with eye/eye-off icons
- **Visual validation indicators** (Check/X icons) for path existence checks
- **Hardcoded env var list:** OPENAI_API_KEY, OPENAI_BASE_URL, HERMES_AGENT_REPO
- **Styling:** Uses glass-card class, Tailwind-like classes, Lucide React icons

## Structure / Sections

1. **System Paths** — Displays Hermes Agent Repo, Evolution Engine paths with existence checks; shows skills count
2. **Environment Variables** — Lists sensitive config (API keys, endpoints) with show/hide toggle functionality

## Notable Entities & Patterns

| Entity | Purpose |
|--------|---------|
| `EnvVar` interface | `{ key, value, desc }` shape for env display |
| `fetchHealth()` | API call to get system status from `@/lib/api` |
| `showKeys` state | Record toggle for masking/unmasking values |
| Health object | `{ status, hermes_repo, hermes_repo_exists, evolution_dir, evolution_dir_exists, skills_count }` |

## Decisions

- Health data is fetched silently (empty catch block) — no user feedback on failure
- Env vars are hardcoded/static list, not dynamically loaded from backend
- Keys masked by default as `"••••••••••••"` placeholder
- Path existence shown with green checkmark or red X icons