---
children_hash: b619fb96a0b08ac7bd129f1d7c125d830caeb4ba9111d31a8938bbf1868eb497
compression_ratio: 0.21685082872928177
condensation_order: 0
covers: [sidebar_navigation_component.md]
covers_token_total: 1448
summary_level: d0
token_count: 314
type: summary
---
## Sidebar Navigation Component

**Source:** `src/components/Sidebar.tsx`

### Overview
Collapsible sidebar providing navigation across 7 main sections with environment status, theme support, and animated transitions.

### Navigation Structure
7 navigation items with icons:
- Overview (Layers)
- Skill Hub (Sparkles)
- Evolution (GitBranch)
- Datasets (Database)
- Metrics (BarChart3)
- Live Logs (Terminal)
- Settings (Settings)

### Props Interface
```
activePage: Page
onNavigate: (page: Page) => void
```

### Page Type Definition
```typescript
export type Page = "overview" | "skills" | "evolution" | "datasets" | "metrics" | "logs" | "settings";
```

### Visual Design
- Collapsed width: 64px, Expanded: 240px
- Animated width transition (0.2s easeOut) via Framer Motion
- Logo with DNA icon and "Hermes Evolution Dashboard" branding
- Active state: cyan highlight with text-[#0891B2] accent
- Hover states with subtle cyan tint on both light/dark themes
- Collapse toggle button at bottom

### Key Features
- AnimatePresence for label fade in/out on collapse
- Sticky positioning (h-screen, top-0)
- Scrollable nav area (flex-1, overflow-y-auto)
- Dual theme support: light (bg-[#E8F9FA]) / dark (bg-[#061014])
- Cyan border accents with 20% opacity