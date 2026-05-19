---
title: Sidebar
summary: ''
tags: []
related: []
keywords: []
createdAt: '2026-04-28T01:33:30.557Z'
updatedAt: '2026-04-28T01:33:30.557Z'
---
## Reason
Preserving complete src/components/Sidebar.tsx from hermes-dashboard project

## Raw Concept
**Task:**
Preserve src/components/Sidebar.tsx

**Files:**
- src/components/Sidebar.tsx

**Timestamp:** 2026-04-28

**Patterns:**
- `Sidebar` - Component or function

## Narrative
### Structure
TSX file with 1 components/functions

### Highlights
Source: hermes-dashboard/src/components/Sidebar.tsx

---


&quot;use client&quot;;

import { useState } from &quot;react&quot;;
import { motion, AnimatePresence } from &quot;framer-motion&quot;;
import {
  Layers,
  GitBranch,
  Database,
  Brain,
  BarChart3,
  Terminal as TerminalIcon,
  Settings,
  Dna,
  ChevronLeft,
  ChevronRight,
  Cpu,
  BookOpen,
  Bot,
  Sparkles,
} from &quot;lucide-react&quot;;

export type Page =
  | &quot;overview&quot;
  | &quot;skills&quot;
  | &quot;evolution&quot;
  | &quot;datasets&quot;
  | &quot;memory&quot;
  | &quot;metrics&quot;
  | &quot;logs&quot;
  | &quot;settings&quot;
;

interface NavItem {
  id: Page;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { id: &quot;overview&quot;, label: &quot;Overview&quot;, icon: &lt;Layers className=&quot;w-4 h-4&quot; /&gt; },
  { id: &quot;skills&quot;, label: &quot;Skill Hub&quot;, icon: &lt;Sparkles className=&quot;w-4 h-4&quot; /&gt; },
  { id: &quot;evolution&quot;, label: &quot;Evolution&quot;, icon: &lt;GitBranch className=&quot;w-4 h-4&quot; /&gt; },
  { id: &quot;datasets&quot;, label: &quot;Datasets&quot;, icon: &lt;Database className=&quot;w-4 h-4&quot; /&gt; },
  { id: &quot;memory&quot;, label: &quot;Memory&quot;, icon: &lt;Brain className=&quot;w-4 h-4&quot; /&gt; },
  { id: &quot;metrics&quot;, label: &quot;Metrics&quot;, icon: &lt;BarChart3 className=&quot;w-4 h-4&quot; /&gt; },
  { id: &quot;logs&quot;, label: &quot;Live Logs&quot;, icon: &lt;TerminalIcon className=&quot;w-4 h-4&quot; /&gt; },
  { id: &quot;settings&quot;, label: &quot;Settings&quot;, icon: &lt;Settings className=&quot;w-4 h-4&quot; /&gt; },
];

interface SidebarProps {
  activePage: Page;
  onNavigate: (page: Page) =&gt; void;
}

export default function Sidebar({ activePage, onNavigate }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    &lt;motion.aside
      animate={{ width: collapsed ? 64 : 240 }}
      transition={{ duration: 0.2, ease: &quot;easeOut&quot; }}
      className=&quot;h-screen sticky top-0 flex flex-col border-r border-[#B2FFFF]/20 bg-[#E8F9FA] dark:bg-[#061014] backdrop-blur-xl transition-colors duration-300&quot;
    &gt;
      {/* Logo */}
      &lt;div className=&quot;flex items-center gap-3 px-4 h-16 border-b border-[#B2FFFF]/15 dark:border-white/[0.06]&quot;&gt;
        &lt;div className=&quot;w-8 h-8 rounded-lg bg-[#0891B2] dark:bg-[#06B6D4] flex items-center justify-center flex-shrink-0 shadow-sm shadow-[#0891B2]/20&quot;&gt;
          &lt;Dna className=&quot;w-4 h-4 text-white&quot; /&gt;
        &lt;/div&gt;
        &lt;AnimatePresence&gt;
          {!collapsed &amp;&amp; (
            &lt;motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className=&quot;overflow-hidden&quot;
            &gt;
              &lt;span className=&quot;text-sm font-semibold tracking-tight text-[#0F172A] dark:text-white&quot;&gt;Hermes&lt;/span&gt;
              &lt;p className=&quot;text-[10px] text-[#475569] dark:text-slate-400&quot;&gt;Evolution Dashboard&lt;/p&gt;
            &lt;/motion.div&gt;
          )}
        &lt;/AnimatePresence&gt;
      &lt;/div&gt;

      {/* Nav items */}
      &lt;nav className=&quot;flex-1 py-4 px-2 space-y-1 overflow-y-auto&quot;&gt;
        {navItems.map((item) =&gt; (
          &lt;button
            key={item.id}
            onClick={() =&gt; onNavigate(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200 ${
              activePage === item.id
                ? &quot;bg-[#B2FFFF]/40 text-[#0E7490] dark:bg-[#B2FFFF]/20 dark:text-[#E0FFFF] shadow-sm shadow-[#B2FFFF]/10&quot;
                : &quot;text-[#475569] hover:text-[#0F172A] hover:bg-[#B2FFFF]/20 dark:text-[#B2FFFF] dark:hover:text-[#E0FFFF] dark:hover:bg-[#B2FFFF]/10&quot;
            }`}
          &gt;
            &lt;span
              className={`flex-shrink-0 ${
                activePage === item.id ? &quot;text-[#0891B2] dark:text-[#67E8F9]&quot; : &quot;&quot;
              }`}
            &gt;
              {item.icon}
            &lt;/span&gt;
            &lt;AnimatePresence&gt;
              {!collapsed &amp;&amp; (
                &lt;motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className=&quot;truncate font-medium&quot;
                &gt;
                  {item.label}
                &lt;/motion.span&gt;
              )}
            &lt;/AnimatePresence&gt;
          &lt;/button&gt;
        ))}
      &lt;/nav&gt;

      {/* Collapse toggle */}
      &lt;div className=&quot;p-2 border-t border-[#B2FFFF]/15 dark:border-[#B2FFFF]/10&quot;&gt;
        &lt;button
          onClick={() =&gt; setCollapsed(!collapsed)}
          className=&quot;w-full flex items-center justify-center p-2 rounded-xl text-[#475569] hover:text-[#0F172A] hover:bg-[#B2FFFF]/20 dark:text-[#A5F3FC]/70 dark:hover:text-[#E0FFFF] dark:hover:bg-[#B2FFFF]/10 transition-colors&quot;
        &gt;
          {collapsed ? (
            &lt;ChevronRight className=&quot;w-4 h-4&quot; /&gt;
          ) : (
            &lt;ChevronLeft className=&quot;w-4 h-4&quot; /&gt;
          )}
        &lt;/button&gt;
      &lt;/div&gt;
    &lt;/motion.aside&gt;
  );
}

    
