## Key Points

- **Sidebar component** from `hermes-dashboard` project - a collapsible navigation sidebar with animated transitions
- **Navigation structure** supports 8 pages: Overview, Skill Hub, Evolution, Datasets, Memory, Metrics, Live Logs, and Settings
- **Built with React + TypeScript**, using `framer-motion` for smooth expand/collapse animations and `lucide-react` for icons
- **Features collapse toggle** that animates width from 240px to 64px with a 0.2s easeOut transition
- **Dark mode support** via CSS custom properties (`dark:bg-[#061014]`, `dark:text-[#E0FFFF]`)
- **Active page highlighting** with cyan tint backgrounds and shadow effects
- **Uses `"use client"`** directive, indicating this is a client-side component in a Next.js app

## Structure / Sections Summary

1. **Type Definitions**
   - `Page` union type for 8 distinct routes
   - `NavItem` interface with `id`, `label`, and `icon` properties

2. **Navigation Data**
   - `navItems` array mapping each page to a label and lucide icon

3. **Component Props**
   - `SidebarProps` interface accepting `activePage` and `onNavigate` callback

4. **Main Component**
   - `Sidebar` function with local `collapsed` state
   - Renders animated