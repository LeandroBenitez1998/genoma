# Sidebar Navigation Component Overview

## Key Points

- **React "use client" component** using Next.js with Framer Motion for smooth animations
- **Collapsible sidebar** toggles between expanded (240px) and collapsed (64px) states with 0.2s ease-out transition
- **7 navigation items**: Overview, Skills, Evolution, Datasets, Metrics, Live Logs, Settings — each with unique Lucide icon
- **Dark mode support** with dual color token sets for light (`#E8F9FA`, `#B2FFFF`) and dark (`#061014`, `#06B6D4`) themes
- **Active page highlighting** with distinct cyan-teal styling (`#0891B2`) and shadow effects
- **Logo branding**: "Hermes/Evolution Dashboard" with DNA helix icon in rounded container
- Props interface exposes `activePage` and `onNavigate` callback for parent-controlled routing

## Structure / Sections

| Section | Purpose |
|---------|---------|
| **Logo Header** | DNA icon + "Hermes/Evolution Dashboard" branding with border separator |
| **Navigation** | 7 nav buttons with icons, labels, hover/active states |
| **Collapse Toggle** | ChevronLeft/Right button to expand/collapse sidebar |

## Notable Entities & Patterns

- **Page type**: Union type literal (`"overview" | "skills" | "evolution" | ...`)
- **NavItem interface**: `{ id: Page, label: string, icon: React.ReactNode }`
- **Animation pattern**: `AnimatePresence` wrapping conditional labels with `initial`/`animate`/`exit` variants
- **Color scheme**: Cyan-teal palette — `#B2FFFF` (accent), `#0891B2` (primary), `#67E8F9` (dark active)
- **Hover states**: Semi-transparent cyan overlays (`/20`, `/10` opacity)
- **Backdrop blur**: `backdrop-blur-xl` on sidebar background

## File

`src/components/Sidebar.tsx`