# Agent-Agnostic Evolution Dashboard — Design Specification

**Date:** 2026-05-19
**Version:** 1.0
**Scope:** Desktop dashboard para monitoreo y evaluación de runs de cualquier agente AI
**Target:** Control-room aesthetic, engineer-facing, high data density

---

## 1. Purpose & Goals

Dashboard para visualizar y comparar ejecuciones de múltiples agentes (Hermes, Claude Code, Codex, etc.) evaluadas por el motor Promethean. Permite:

1. **Ingenieros de agentes** — Ver performance cross-agent, detectar regresiones
2. **Skill developers** — Comparar baseline vs evolved, aprobar/rechazar evoluciones
3. **Operaciones** — Monitorear tasas de éxito, costos de tokens, efficiency

**Success Criteria:**
- Datos de cualquier agente visibles con el mismo formato
- Regresiones detectadas visualmente sin fricción
- Aggregate score + scorer breakdown accesibles en ≤2 clicks
- Consistent con Hermes control-room design system

---

## 2. Design System (Herencia)

Mismo sistema que `hermes_dashboard/DESIGN.md`:

| Token | Valor |
|---|---|
| Primary | `#002444` (Navy) |
| Secondary | `#a93800` (Orange accent) |
| Surface | `#faf9fc` (Warm White) |
| On-surface | `#1a1c1e` |
| On-surface-variant | `#43474e` |
| Success | `#4caf50` |
| Warning | `#ffc107` |
| Error | `#ba1a1a` |
| Outline | `#73777f` |

**Typography:**
- Headlines: Inter 600, 20px (headline-sm)
- Body: Inter 400, 14px (body-md)
- Data/mono: JetBrains Mono 400, 12px
- Caps label: Inter 700, 11px, 0.05em tracking

**Spacing:** 8px base unit. Container padding 24px. Table rows 32–40px.

---

## 3. Layout & Navigation

### 3.1 Global Header (56px)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [◈] GENOMA          ●  All Systems Active — last sync 3s ago    [👤 Leandro]│
└────────────────────────────────────────────────────────────────────────────┘
```

- Fondo: Navy `#002444`
- Logo + "GENOMA" en Inter 600, white
- Status dot: green cuando backend online, red cuando offline
- Text: "All Systems Active" / "Backend Unavailable" + timestamp relativo

### 3.2 Tab Navigation (48px, sticky)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  Agents │  Runs │  Regression │  Scorers                                   │
└────────────────────────────────────────────────────────────────────────────┘
```

- Active tab: underline navy 3px, Inter 600
- Inactive: `#73777f`, Inter 400
- Surface background, 1px bottom border

### 3.3 Content Layout

```
┌────────────────┬─────────────────────────────────────────────────────────┐
│   Sidebar      │                   Main Content                           │
│   256px fixed  │   fluid (max-width 1440px)                               │
│                │                                                           │
│   Filters      │   Page content here                                      │
│   Agent list   │                                                           │
│   Quick stats  │                                                           │
└────────────────┴─────────────────────────────────────────────────────────┘
```

---

## 4. Screens

### Screen 1: Agents Overview (`/agents`)

Vista principal. Muestra performance cross-agent con stat cards + tabla.

#### 4.1.1 Stat Cards Row (4 cards)

```
┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ AGENTS         │ │ TOTAL RUNS     │ │ AVG SUCCESS    │ │ AVG AGG. SCORE │
│ mono: 3        │ │ mono: 1,247    │ │ mono: 87.4%    │ │ mono: 0.83     │
│ ────────────── │ │ ────────────── │ │ ────────────── │ │ ────────────── │
│ [sparkline]    │ │ [sparkline]    │ │ [sparkline]    │ │ [sparkline]    │
└────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘
```

- Label: `label-caps` typography, `#43474e`
- Value: `mono-data` typography (JetBrains Mono), `#1a1c1e`, 28px
- Sparkline: 40px height, navy line, last 30 days
- Border: 1px solid `#002444` at 10% opacity

#### 4.1.2 Agent Table

```
┌──────────────────────────────────────────────────────────────────────────┐
│ AGENT            RUNS   SUCCESS   AVG TOKENS  AGG SCORE   LAST RUN       │
├──────────────────────────────────────────────────────────────────────────┤
│ ● hermes         524    94.2%     6,240       0.89        2m ago         │
│ ○ claude-code    412    85.1%     8,100       0.81        15m ago        │
│ ○ codex          311    79.3%     9,800       0.76        1h ago         │
└──────────────────────────────────────────────────────────────────────────┘
```

- Row height: 40px
- Agent status dot: ● green = active (run <1h), ○ gray = idle
- Agent name: Inter 500, `#1a1c1e`
- Numeric data: JetBrains Mono, `#43474e`
- AGG SCORE column: color-coded pill
  - `> 0.85` → navy bg, white text
  - `0.65–0.85` → warning yellow bg
  - `< 0.65` → error red bg
- Row hover: `#f4f3f6` background tint
- Clickable row → navigates to runs filtered by agent

#### 4.1.3 Score Distribution Chart (right panel, 340px)

```
┌─────────────────────────────────────────┐
│ SCORE DISTRIBUTION                      │
│                                         │
│  hermes      ████████████████ 0.89      │
│  claude-code ████████████     0.81      │
│  codex       ██████████       0.76      │
│                                         │
│ BY SCORER:                              │
│  outcome       ████████████████ 0.91   │
│  tool_eff      ████████        0.68    │
│  token_cost    █████████████   0.84    │
│  error_recov   ████████████    0.80    │
└─────────────────────────────────────────┘
```

- Horizontal bar chart
- Bar fill: navy gradient (left) → lighter navy (right)
- Value label: JetBrains Mono, right-aligned

---

### Screen 2: Runs List (`/runs`)

Tabla de todas las runs con filtros y evaluación inline.

#### 4.2.1 Filter Bar

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [Agent ▾]  [Outcome ▾]  [Since: 7d ▾]  [Scorer ▾]  ────────  [↓ Export]  │
└────────────────────────────────────────────────────────────────────────────┘
```

- Dropdowns: Inter 14px, 1px navy border, 4px radius
- Active filter: navy bg + white text
- Export: secondary button (1px navy border)

#### 4.2.2 Runs Table

```
┌───┬──────────┬─────────────┬────────────────────────┬─────────┬──────────┬───────┐
│   │ RUN ID   │ AGENT       │ TASK                   │ OUTCOME │ AGG SCORE│ TIME  │
├───┼──────────┼─────────────┼────────────────────────┼─────────┼──────────┼───────┤
│ □ │ run-001  │ hermes      │ Refactor auth module   │ ✓ success│ 0.91    │ 2m    │
│ □ │ run-002  │ claude-code │ Fix N+1 query in list  │ ✓ success│ 0.84    │ 15m   │
│ □ │ run-003  │ claude-code │ Add dark mode toggle   │ ✗ failure│ 0.21    │ 23m   │
│ □ │ run-004  │ hermes      │ Optimize skill prompt  │ ~ partial│ 0.55    │ 45m   │
└───┴──────────┴─────────────┴────────────────────────┴─────────┴──────────┴───────┘
```

- RUN ID: JetBrains Mono, `#73777f`, 10 chars truncated
- TASK: Inter 400, truncated at 40 chars, tooltip on hover
- OUTCOME pill:
  - `success` → `#4caf50` text + `rgba(76,175,80,0.1)` bg
  - `failure` → `#ba1a1a` text + `rgba(186,26,26,0.1)` bg
  - `partial` → `#ffc107` text + `rgba(255,193,7,0.1)` bg
- AGG SCORE: navy pill si >0.85, warning si 0.65–0.85, error si <0.65
- Checkbox: multi-select para batch compare
- Row click → Run Detail drawer (slide-in desde derecha, 520px)

#### 4.2.3 Pagination

```
                          ← Prev   [1] [2] [3] ... [12]   Next →
                          Showing 1–50 of 584 runs
```

---

### Screen 3: Run Detail Drawer (slide-in, 520px)

Se abre al hacer click en cualquier run. Overlay sobre runs list.

#### 4.3.1 Header

```
┌─────────────────────────────────────────────────────────┬───┐
│ run-001                              ✓ success           │ ✕ │
│ Refactor auth module                 hermes · 2m ago     │   │
└─────────────────────────────────────────────────────────┴───┘
```

- Run ID: JetBrains Mono 13px
- Task name: Inter 600 18px
- Agent + time: Inter 400 13px, `#73777f`
- Close button: 32x32, icon only

#### 4.3.2 Aggregate Score Badge

```
┌──────────────────────────────────────────┐
│          AGGREGATE SCORE                  │
│               0.91                        │
│    ████████████████████████████░░░░       │
└──────────────────────────────────────────┘
```

- Score: JetBrains Mono, 40px, navy
- Progress bar: 8px height, navy fill, `#e3e2e5` track
- Label: label-caps

#### 4.3.3 Scorer Breakdown

```
┌──────────────────────────────────────────────────────────┐
│ SCORER BREAKDOWN                                          │
├───────────────────┬────────┬────────┬────────────────────┤
│ SCORER            │ SCORE  │ PASSED │ DETAILS            │
├───────────────────┼────────┼────────┼────────────────────┤
│ outcome           │  1.00  │  ✓     │ outcome: success   │
│ tool_efficiency   │  0.67  │  ✓     │ 2 unique / 3 total │
│ token_cost        │  0.86  │  ✓     │ 7,000 / 50,000     │
│ error_recovery    │  1.00  │  ✓     │ 0 errors           │
├───────────────────┼────────┼────────┼────────────────────┤
│ AGGREGATE         │  0.91  │        │                    │
└───────────────────┴────────┴────────┴────────────────────┘
```

- Score: JetBrains Mono
- Passed: ✓ green icon / ✗ red icon
- Details: JetBrains Mono 11px, `#73777f`
- Footer row: bold, navy background tint

#### 4.3.4 Metrics Panel

```
┌──────────────────────────────────────────┐
│ METRICS                                  │
│                                          │
│  input_tokens   5,000                    │
│  output_tokens  2,000                    │
│  total_tokens   7,000                    │
│  tool_calls     3                        │
│  latency_ms     1,420ms                  │
└──────────────────────────────────────────┘
```

#### 4.3.5 Tool Calls (expandable)

```
┌──────────────────────────────────────────┐
│ TOOL CALLS (3)                      ▾    │
├──────────────────────────────────────────┤
│ Read    id:1   150ms   input_summary...  │
│ Edit    id:2   200ms   path: auth.ts     │
│ Read    id:3   80ms    input_summary...  │
└──────────────────────────────────────────┘
```

#### 4.3.6 Errors Panel (solo si errors.length > 0)

```
┌──────────────────────────────────────────┐
│ ERRORS (1)                          ▾    │
├──────────────────────────────────────────┤
│ ⚠ TypeError: Cannot read prop 'x'       │
│   message: expected number, got string  │
└──────────────────────────────────────────┘
```

- Error header: orange `#a93800`
- Error text: JetBrains Mono 11px

#### 4.3.7 Actions Footer

```
┌──────────────────────────────────────────┐
│  [Re-evaluate]     [Compare with...]     │
└──────────────────────────────────────────┘
```

- Re-evaluate: primary navy button
- Compare with: secondary button → opens compare modal

---

### Screen 4: Regression Comparison (`/regression`)

Comparación side-by-side de dos runs para detectar mejoras o regresiones.

#### 4.4.1 Run Selector

```
┌────────────────────────────────────────────────────────────────────────────┐
│  BASELINE                          EVOLVED                                  │
│  ┌──────────────────────┐         ┌──────────────────────┐                 │
│  │ run-001               ▾│        │ run-002               ▾│               │
│  │ hermes · Refactor auth│        │ hermes · Optimize skill│               │
│  └──────────────────────┘         └──────────────────────┘                 │
│                        [Compare →]                                          │
└────────────────────────────────────────────────────────────────────────────┘
```

#### 4.4.2 Delta Banner (resultado principal)

**Improvement:**
```
┌────────────────────────────────────────────────────────────────────────────┐
│  ▲  IMPROVEMENT DETECTED  +0.07  (threshold: 0.05)                         │
│     Evolved run significantly outperforms baseline                         │
└────────────────────────────────────────────────────────────────────────────┘
```
- Bg: `rgba(76,175,80,0.1)`, border: `#4caf50`, icon: ▲ green

**Regression:**
```
┌────────────────────────────────────────────────────────────────────────────┐
│  ▼  REGRESSION DETECTED  -0.12  (threshold: 0.05)                          │
│     Evolved run scores significantly lower than baseline                   │
└────────────────────────────────────────────────────────────────────────────┘
```
- Bg: `rgba(186,26,26,0.1)`, border: `#ba1a1a`, icon: ▼ red

**Neutral:**
```
┌────────────────────────────────────────────────────────────────────────────┐
│  ●  NEUTRAL  Δ +0.02  (within ±0.05 threshold)                             │
└────────────────────────────────────────────────────────────────────────────┘
```
- Bg: `rgba(115,119,127,0.08)`, border: `#c3c6cf`, icon: ● gray

#### 4.4.3 Side-by-Side Score Comparison

```
┌─────────────────────────────┬─────────────────────────────┬─────────────┐
│         BASELINE             │         EVOLVED              │    DELTA    │
├─────────────────────────────┼─────────────────────────────┼─────────────┤
│ Aggregate     0.84          │ Aggregate     0.91           │   +0.07 ▲   │
├─────────────────────────────┼─────────────────────────────┼─────────────┤
│ outcome       1.00 ✓        │ outcome       1.00 ✓         │   +0.00 ●   │
│ tool_eff      0.45 ✗        │ tool_eff      0.67 ✓         │   +0.22 ▲   │
│ token_cost    0.91 ✓        │ token_cost    0.86 ✓         │   -0.05 ▼   │
│ error_recov   1.00 ✓        │ error_recov   1.00 ✓         │   +0.00 ●   │
└─────────────────────────────┴─────────────────────────────┴─────────────┘
```

- Delta column: color-coded
  - `> 0` → green `#4caf50` + ▲
  - `< 0` → red `#ba1a1a` + ▼
  - `= 0` → gray + ●
- Improved scorer rows: subtle green left border (2px)
- Regressed scorer rows: subtle red left border (2px)

#### 4.4.4 Threshold Control

```
  Threshold  [──────●─────────────────]  0.05
             0.01                        0.20
```

- Slider: navy track, navy thumb
- Value display: JetBrains Mono, live update
- Changing threshold re-runs comparison

---

### Screen 5: Scorers Reference (`/scorers`)

Documentación interactiva de los 5 scorers disponibles.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ SCORERS (5)                                                               │
├──────────────┬──────────────────────────────────────────────┬────────────┤
│ SCORER       │ LOGIC                                         │ APPLIES TO │
├──────────────┼──────────────────────────────────────────────┼────────────┤
│ outcome      │ success=1.0, partial=0.5, failure=0.0         │ all runs   │
│ tool_eff     │ unique_tools / total_calls (pass if >0.3)     │ w/ tools   │
│ token_cost   │ max(0, 1 - tokens/50000)                      │ w/ metrics │
│ error_recov  │ success_no_err=1.0, w_err=0.8, failure=0.0   │ all runs   │
│ delta        │ wraps DeltaValidator (DSPy+GEPA)              │ hermes only│
└──────────────┴──────────────────────────────────────────────┴────────────┘
```

---

## 5. Component Library

### StatusPill

```
● success    ✗ failure    ~ partial    ? unknown
```

| Outcome | Text color | Background | Icon |
|---|---|---|---|
| success | `#4caf50` | `rgba(76,175,80,0.1)` | ✓ |
| failure | `#ba1a1a` | `rgba(186,26,26,0.1)` | ✗ |
| partial | `#ffc107` | `rgba(255,193,7,0.1)` | ~ |
| unknown | `#73777f` | `rgba(115,119,127,0.1)` | ? |

### ScoreBadge

```
0.91  (navy)     0.74  (warning yellow)     0.42  (error red)
```

- JetBrains Mono, 4px radius pill
- Thresholds: `>0.85` navy, `0.65–0.85` warning, `<0.65` error

### AgentChip

```
[◈ hermes]    [≡ claude-code]    [⊕ codex]
```

- 4px radius, 1px border, navy text on white bg
- Icon per agent type
- Hover: navy fill, white text

### DeltaIndicator

```
+0.07 ▲    -0.03 ▼    +0.00 ●
```

- JetBrains Mono
- Positive: `#4caf50`
- Negative: `#ba1a1a`
- Zero: `#73777f`

---

## 6. Empty States

### No runs for agent

```
       ○
       │
  No runs found for this agent.
  Run a collector to ingest data.

  [POST /api/runs/migrate →]
```

### First-time state (no data)

```
    [◈ GENOMA]

  No agents connected yet.
  Migrate existing traces or run a collector.

  [↓ Migrate Hermes traces]   [↓ Collect Claude Code sessions]
```

---

## 7. Responsiveness

Desktop focused (min-width 1024px). Sidebar collapses to icon-only at 1280px. No mobile layout required for MVP.

---

## 8. Interactions

| Trigger | Action |
|---|---|
| Click agent row | Navigate to `/runs?agent=hermes` |
| Click run row | Open Run Detail drawer (slide-in 300ms ease-out) |
| Click [Compare with...] | Open run selector modal → navigate to `/regression` |
| Click scorer row | Tooltip with full details dict |
| Change threshold slider | Debounce 150ms → re-fetch `/api/runs/compare` |
| Click [Re-evaluate] | POST `/api/runs/{id}/evaluate` → refresh scores |
| Click [↓ Export] | Download runs as CSV |

---

## 9. API Binding

| Screen element | API call |
|---|---|
| Stat cards | `GET /api/agents` |
| Agent table | `GET /api/agents` |
| Runs table | `GET /api/runs?...filters` |
| Run Detail scores | `GET /api/runs/{id}/scores` |
| Run Detail evaluate | `POST /api/runs/{id}/evaluate` |
| Regression result | `POST /api/runs/compare` |
| Migration button | `POST /api/runs/migrate` |
