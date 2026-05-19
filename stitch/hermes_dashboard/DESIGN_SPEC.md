# Hermes Dashboard — High-Fidelity Design Specification

**Date:** 2026-05-18  
**Version:** 1.0  
**Scope:** Production-ready HTML/React components for Hermes Dashboard  
**Target:** Control-room aesthetic for engineer-facing system monitoring + skill discovery

---

## 1. Purpose & Goals

Hermes Dashboard is a **hybrid monitoring + control + analytics + skill-discovery** interface serving three user personas:

1. **System Engineers:** Monitor agent health, system metrics, real-time status
2. **Skill Developers:** Analyze skill performance, discover improvement opportunities
3. **Operations:** Execute/retry actions, filter & debug historical task execution

**Success Criteria:**
- Data-dense interface; information parseable without excessive scrolling
- Status & health visible at-a-glance (no hidden states)
- All core interactions (filter, sort, trigger, detail) work without page reload
- Consistent with Hermes control-room design system (navy + orange, Inter + JetBrains Mono)

---

## 2. Design System Constraints

**Colors:**
- Primary: Navy (#002444) — structure, buttons, borders
- Secondary: Orange (#a93800) — high-priority actions, alerts, editable states
- Surface: Warm White (#faf9fc) — background
- Text: On-surface (#1a1c1e) — body text; Mono (#43474e) — data
- Status: Green (#4caf50) — success; Yellow (#ffc107) — warning; Red (#ba1a1a) — error

**Typography:**
- Headlines: Inter, 20px (headline-sm), weight 600
- Body: Inter, 14px (body-md), weight 400
- Data/mono: JetBrains Mono, 12px, weight 400

**Spacing & Grid:**
- 8px base unit
- Gutters: 16px (between columns), 24px (container padding)
- Dense rows: 32–40px height (tables/lists)

**Elevation:**
- Level 0: Surface background
- Level 1: Cards/panels with 1px navy border, no shadow
- Level 2: Popovers/tooltips with 4px blur shadow
- Level 3: Modals with 12px blur shadow + high-contrast border

---

## 3. Layout & Navigation

### 3.1 Global Header
**Height:** 56px  
**Components:**
- Left: Hermes logo + text "Hermes Dashboard"
- Center: Real-time status indicator
  - Indicator dot (green = monitoring, red = paused/error)
  - Text: "Monitoring" or "Paused" + last update timestamp
- Right: User menu (future; placeholder for now)

**Styling:**
- Navy background (#002444)
- White text
- Subtle bottom border (1px, #ccc)

### 3.2 Tab Navigation
**Position:** Below global header, sticky  
**Height:** 48px  
**Components:**
- 4 tabs: **Agents | Skills | Metrics | Actions**
- Active tab: underline (navy, 3px), bold text
- Inactive tabs: gray text (#73777f)
- Hover: subtle background tint

**Styling:**
- Surface background
- 1px bottom border separating from content

### 3.3 Tab Content Area
**Layout:** Full-width below tabs  
**Padding:** 24px (all sides)  
**Max-width:** 1440px (centered)

---

## 4. Tab: AGENTS

### 4.1 Overall Layout
**Hybrid:** Left sidebar (fixed 256px) + Right detail panel (fluid)

### 4.2 Left Sidebar (Tree View)
**Width:** 256px, fixed  
**Background:** Surface container-low (#f4f3f6)  
**Border-right:** 1px navy at 10% opacity  

**Tree Structure:**
```
Hermes [online]
├── Sub-Agent-1 [online] ✓
├── Sub-Agent-2 [offline] ✗
├── Sub-Agent-3 [busy] ⚠
└── Sub-Agent-N
```

**Node Styling:**
- Each node: 40px height, 16px padding, 8px left margin (nesting)
- Text: body-md navy
- Status badge: 8px dot (green/red/yellow) + text
- Hover: background tint
- Click: select + load detail in right panel
- Expand/collapse: chevron icon for nodes with children

**Header (above tree):**
- "AGENTS" label (label-caps)
- Refresh button (navy icon)

### 4.3 Right Detail Panel
**Layout:** Single-column, scrollable  
**Min-width:** 400px  

**Content Sections (stacked vertically):**

**Section A: Agent Identity**
- Heading: Agent name (headline-sm)
- Sub-text: Agent ID (body-sm, gray)
- Status badge (large): online/offline/busy + indicator dot

**Section B: Status Overview**
- 4 stat cards in 2×2 grid:
  - Uptime (%) | Cpu (%) | Memory (%) | Last Action
- Card format: label (body-sm) + value (mono-label, large) + mini sparkline
- Card styling: navy border, surface container bg

**Section C: Recent Skills (Table)**
- Columns: Skill Name | Started | Duration | Status
- Dense rows (32px)
- Up to 5 rows; scrollable if more
- Status icon: ✓/⚠/✗

**Section D: Actions**
- Buttons (navy): "Force Refresh", "View Logs"
- Buttons (orange): "Stop" (if agent is running)

**Default State (no agent selected):**
- Right panel shows "Select an agent to view details"

---

## 5. Tab: SKILLS

### 5.1 Layout
Single-column, full-width table with search & sort

### 5.2 Search & Filter Bar
**Height:** 48px  
**Components:**
- Search input (label: "Search skills")
  - Icon: magnifying glass
  - Placeholder: "Search by name or agent..."
- Sort dropdown (default: "Usage (24h)", descending)

### 5.3 Skills Table
**Columns (7):**
1. Skill Name (text)
2. Used By (agent count, e.g., "3 agents")
3. Usage Count (24h, numeric)
4. Perf Score (0-100, numeric; orange if <70)
5. Avg Exec Time (milliseconds, mono)
6. Errors (count; red if >0)
7. Last Run (relative time, e.g., "5m ago")

**Row Height:** 32px  
**Row Dividers:** 1px navy at 5% opacity  
**Hover State:** Background tint, slight lift  

**Column Sorting:**
- Click header to sort ascending/descending
- Indicator: up/down arrow next to active column name

**Status Styling:**
- Perf Score <70: orange text
- Errors >0: red dot + count
- Success: green checkmark (implicit in "Errors" column showing 0)

**Pagination:**
- Bottom: "Showing X–Y of Z | < Previous | Next >"
- 50 rows per page

---

## 6. Tab: METRICS

### 6.1 Layout
Two-tier: Top stat cards + below time-series charts

### 6.2 Stat Cards Section
**Grid:** 4 columns (responsive: 2 cols on tablet, 1 on mobile)  
**Card Height:** 120px  
**Card Content:**
- Label (body-sm, gray): "CPU Usage", "Memory", "Latency (ms)", "Error Rate (%)"
- Value (mono-label, large, navy): e.g., "45.2%", "2048 MB", "234ms", "1.3%"
- Mini sparkline (8×30px, navy line, transparent fill, bottom-right corner)
- Card styling: navy border (1px), surface container bg

**Card Hover:**
- Slight shadow lift
- Tooltip on sparkline: hover point shows timestamp + value

### 6.3 Charts Section
**Grid:** 2 columns (1 on mobile)  
**Chart Height:** 300px each

**Chart A: Resource Usage (CPU & Memory)**
- X-axis: Time (last 24h, labels every 4h)
- Y-axis: % (0-100)
- Lines: CPU (navy), Memory (orange)
- Grid: subtle navy lines (1px, 10% opacity)
- Legend: below chart
- Interaction: Hover shows tooltip (timestamp + values for both metrics)

**Chart B: Latency & Errors**
- X-axis: Time (last 24h)
- Y-axis (left): Latency (ms), Y-axis (right): Error Rate (%)
- Lines: Latency (navy), Error Rate (orange)
- Legend: below chart
- Interaction: Hover tooltip

**Chart Library:**
- Recommend: Recharts (React) or Chart.js (vanilla)
- Styling: navy/orange colors from design system

---

## 7. Tab: ACTIONS

### 7.1 Layout
Filter bar + action log table

### 7.2 Filter Bar
**Height:** 56px  
**Components:**

- **Agent Filter (multi-select dropdown):**
  - Label: "Agent"
  - Placeholder: "All agents"
  - Shows selected count, e.g., "2 selected"

- **Skill Filter (multi-select dropdown):**
  - Label: "Skill"
  - Placeholder: "All skills"

- **Status Filter (dropdown):**
  - Label: "Status"
  - Options: All | Success ✓ | Error ✗ | Pending ⏳

- **Date Range Picker:**
  - Label: "Date Range"
  - Buttons: "Last 24h", "Last 7d", "Custom"
  - Custom: start & end date inputs

- **Clear Filters Button:**
  - Navy text, no bg

**Styling:** Flex row, 16px gaps, wrap on mobile

### 7.3 Action Log Table
**Columns (7):**
1. Timestamp (relative + full on hover, e.g., "5m ago")
2. Agent Name (text)
3. Skill Name (text)
4. Status (icon + text; ✓/⚠/✗)
5. Duration (milliseconds, mono)
6. Result (truncated text; full on modal)
7. Actions (button: "Details" or "Retry")

**Row Height:** 40px  
**Row Dividers:** 1px navy at 5% opacity  
**Row Hover:**
- Background tint
- Status icon highlights (orange if error)

**Status Badges:**
- Success: green checkmark + "Success"
- Error: red X + "Error"
- Pending: orange hourglass + "Pending"

**Actions Column:**
- "Details" button: opens modal with full result/logs
- "Retry" button (orange): retry the action (if applicable)

**Pagination:**
- 50 rows per page

---

## 8. Components (Reusable)

### 8.1 Buttons
- **Primary (Navy):** solid navy bg, white text, 4px radius
- **Secondary (Ghost):** navy border, transparent bg, navy text
- **Tertiary/Action (Orange):** solid orange bg, white text, 4px radius
- **Disabled:** gray bg, gray text, cursor not-allowed

### 8.2 Status Badge
- Dot (8px circle) + text
- Colors: green (#4caf50), yellow (#ffc107), red (#ba1a1a)

### 8.3 Stat Card
- Navy border (1px), surface bg, 24px padding
- Label (body-sm, gray) + Value (mono-label, large, navy) + sparkline

### 8.4 Table Row
- 32–40px height
- Navy divider (1px)
- Hover tint
- Clickable (cursor pointer, selection highlight)

### 8.5 Dropdown / Multi-Select
- Navy border (1px) on focus
- Chevron icon (right)
- Placeholder text (gray)

### 8.6 Modal
- Navy border (3px), shadow (12px blur)
- Header: title + close button
- Body: scrollable content
- Footer: action buttons (cancel, confirm)

---

## 9. Interaction & Behavior

### 9.1 Tab Switching
- Instant (no loading state)
- URL updates (e.g., `/dashboard#agents`)
- Selected tab persists on page reload

### 9.2 Agents Tab
- Click agent in tree → load details in right panel (smooth transition)
- Right panel is scrollable if content exceeds viewport height
- Buttons (refresh, stop) perform actions, show loading state + success/error toast

### 9.3 Skills Tab
- Sort/filter: instant (client-side if <1000 rows, else debounced API call)
- Click skill name: opens detail modal with full metrics, optimization suggestions, edit button

### 9.4 Metrics Tab
- Charts auto-refresh every 30 seconds (WebSocket or polling)
- Stat cards reflect latest values
- Hover on sparkline/chart: tooltip with exact values

### 9.5 Actions Tab
- Filter/sort: instant or debounced API call
- "Details" button: modal with full logs, error stack, full result text
- "Retry" button: trigger re-execution, show loading state + result toast

### 9.6 Global Refresh
- Header status indicator shows "updating..." during refresh
- Refresh completes in <2s (or shows "refresh failed" in orange)

---

## 10. Responsive Behavior

### 10.1 Desktop (1440px+)
- Full layout as described

### 10.2 Tablet (768–1024px)
- Sidebar width reduced to 200px (Agents tab)
- Charts stack vertically (Metrics tab)
- Table columns: prioritize Agent, Skill, Status; hide Duration/Result (available in detail)

### 10.3 Mobile (<768px)
- Sidebar hidden; menu button (☰) toggles tree
- Single-column layout
- Tables: horizontal scroll or card layout per row
- Dropdowns: native mobile select

---

## 11. Data Structures (Mock)

### Agent Object
```json
{
  "id": "agent-001",
  "name": "Sub-Agent-1",
  "status": "online",
  "uptime_percent": 99.5,
  "cpu_percent": 45.2,
  "memory_mb": 512,
  "last_action": "2026-05-18T15:30:00Z",
  "recent_skills": [
    { "name": "brainstorm", "started": "...", "duration": 1200, "status": "success" },
    ...
  ]
}
```

### Skill Object
```json
{
  "id": "skill-001",
  "name": "brainstorm",
  "used_by": 3,
  "usage_count_24h": 42,
  "perf_score": 85,
  "avg_exec_time_ms": 1200,
  "errors_count": 0,
  "last_run": "2026-05-18T15:28:00Z"
}
```

### Action Object
```json
{
  "id": "action-001",
  "timestamp": "2026-05-18T15:30:00Z",
  "agent_name": "Sub-Agent-1",
  "skill_name": "brainstorm",
  "status": "success",
  "duration_ms": 1500,
  "result": "Design proposal generated",
  "full_logs": "..."
}
```

---

## 12. Future Enhancements (Out of Scope)

- Skill improvement workflows (edit, test, deploy)
- Real-time WebSocket updates
- Export/reporting (CSV, PDF)
- Alerting rules & notifications
- Dark mode
- Accessibility (WCAG AA)

---

## 13. Implementation Notes

- **Framework:** React 19 recommended (component-based, hooks)
- **Styling:** Tailwind CSS + custom CSS vars for design system colors
- **Charts:** Recharts (lightweight, Recharts-React integration)
- **Icons:** Lucide React
- **State Management:** React Context or Zustand (lightweight)
- **API Integration:** Placeholder endpoints; integrate with actual Hermes API once available

---

**End of Specification**
