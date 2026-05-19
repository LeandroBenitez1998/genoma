"use client"

import * as React from "react"
import {
  Layers,
  GitBranch,
  Database,
  BarChart3,
  Terminal,
  Settings,
  Dna,
  Sparkles,
  Cpu,
  Bot,
  BookOpen,
} from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { useTheme } from "next-themes"
import { cn } from "@/lib/utils"

// ── Navigation Config ─────────────────────────────────────────────────
export type Page =
  | "overview"
  | "skills"
  | "evolution"
  | "datasets"
  | "metrics"
  | "logs"
  | "settings"
  | "curator"

interface NavItem {
  id: Page
  label: string
  icon: React.ElementType
  section: "main" | "tools" | "system"
}

const navItems: NavItem[] = [
  { id: "overview", label: "Overview", icon: Layers, section: "main" },
  { id: "skills", label: "Skill Hub", icon: Sparkles, section: "main" },
  { id: "evolution", label: "Evolution", icon: GitBranch, section: "main" },
  { id: "datasets", label: "Datasets", icon: Database, section: "tools" },
  { id: "metrics", label: "Metrics", icon: BarChart3, section: "tools" },
  { id: "logs", label: "Live Logs", icon: Terminal, section: "tools" },
  { id: "curator", label: "Curator", icon: Dna, section: "system" },
  { id: "settings", label: "Settings", icon: Settings, section: "system" },
]

// ── Genoma Logo ───────────────────────────────────────────────────────
function GenomaLogo({ collapsed }: { collapsed: boolean }) {
  return (
    <div className="flex items-center gap-3 px-2">
      {/* Logo mark — always visible */}
      <div className="relative flex-shrink-0">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center
          bg-gradient-to-br from-[#002444] to-[#1a3a5c]
          shadow-lg shadow-[#002444]/20
          dark:from-[#1a3a5c] dark:to-[#002444]">
          <Dna className="w-5 h-5 text-[#fcf9f8]" />
        </div>
        {/* Streak dot — Genoma tertiary */}
        <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full
          bg-[#ffb94c] border-2 border-sidebar" />
      </div>

      {/* Text — hidden when collapsed */}
      {!collapsed && (
        <div className="overflow-hidden min-w-0">
          <p className="text-sm font-semibold tracking-tight text-sidebar-foreground truncate">
            Genoma
          </p>
          <p className="text-[10px] text-sidebar-foreground/50 truncate">
            Agent Evolution Dashboard
          </p>
        </div>
      )}
    </div>
  )
}

// ── Nav Section ───────────────────────────────────────────────────────
function NavSection({
  title,
  items,
  activePage,
  onNavigate,
}: {
  title: string
  items: NavItem[]
  activePage: Page
  onNavigate: (page: Page) => void
}) {
  const { state } = useSidebar()
  const collapsed = state === "collapsed"

  return (
    <SidebarGroup>
      {!collapsed && (
        <SidebarGroupLabel className="text-[10px] uppercase tracking-[0.15em] text-sidebar-foreground/40 px-3 mb-1">
          {title}
        </SidebarGroupLabel>
      )}
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => {
            const isActive = activePage === item.id
            return (
              <SidebarMenuItem key={item.id}>
                <SidebarMenuButton
                  tooltip={collapsed ? item.label : undefined}
                  isActive={isActive}
                  onClick={() => onNavigate(item.id)}
                  className={cn(
                    "transition-all duration-200",
                    isActive && [
                      "bg-gradient-to-r from-[#a93800]/15 to-transparent",
                      "text-sidebar-foreground font-medium",
                      "border-l-[3px] border-l-[#a93800]",
                      "shadow-[inset_0_0_0_1px_rgba(169,56,0,0.08)]",
                    ],
                    !isActive && [
                      "text-sidebar-foreground/60 hover:text-sidebar-foreground/90",
                      "hover:bg-sidebar-accent/50",
                      "border-l-[3px] border-l-transparent",
                    ]
                  )}
                >
                  <item.icon
                    className={cn(
                      "h-4 w-4 flex-shrink-0",
                      isActive && "text-[#a93800]"
                    )}
                  />
                  <span className="truncate">{item.label}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}

// ── AppSidebar (inner) ─────────────────────────────────────────────────
function AppSidebarInner({
  activePage,
  onNavigate,
}: {
  activePage: Page
  onNavigate: (page: Page) => void
}) {
  const { state } = useSidebar()
  const collapsed = state === "collapsed"

  const mainItems = navItems.filter((i) => i.section === "main")
  const toolItems = navItems.filter((i) => i.section === "tools")
  const systemItems = navItems.filter((i) => i.section === "system")

  return (
    <Sidebar
      collapsible="icon"
      className={cn(
        "border-r-0",
        // Genoma glass sidebar
        "bg-[#002444]/95 dark:bg-[#001830]/95",
        "backdrop-blur-2xl",
        // Subtle inner highlight
        "shadow-[inset_-1px_0_0_rgba(255,255,255,0.04)]",
      )}
    >
      {/* ── Header ── */}
      <SidebarHeader className="h-16 flex items-center border-b border-sidebar-border/20 px-3">
        <GenomaLogo collapsed={collapsed} />
      </SidebarHeader>

      {/* ── Content ── */}
      <SidebarContent className="py-3">
        <NavSection title="Core" items={mainItems} activePage={activePage} onNavigate={onNavigate} />
        <NavSection title="Analysis" items={toolItems} activePage={activePage} onNavigate={onNavigate} />
        <NavSection title="System" items={systemItems} activePage={activePage} onNavigate={onNavigate} />
      </SidebarContent>

      {/* ── Footer ── */}
      <SidebarFooter className="border-t border-sidebar-border/20 p-2">
        <div className={cn(
          "flex items-center gap-2 px-2 py-1.5 rounded-lg",
          "text-[10px] text-sidebar-foreground/30",
          collapsed && "justify-center"
        )}>
          <div className="w-1.5 h-1.5 rounded-full bg-[#22c55e] led-pulse" style={{color: "#22c55e"}} />
          {!collapsed && <span className="truncate">Backend online</span>}
        </div>
      </SidebarFooter>

      <SidebarRail className="hover:after:bg-[#a93800]/20 after:bg-sidebar-border/20" />
    </Sidebar>
  )
}

// ── Main Sidebar (with Provider) ──────────────────────────────────────
export interface AppSidebarProps {
  activePage: Page
  onNavigate: (page: Page) => void
  children?: React.ReactNode
}

export default function AppSidebar({
  activePage,
  onNavigate,
  children,
}: AppSidebarProps) {
  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex h-screen w-full overflow-hidden">
        <AppSidebarInner activePage={activePage} onNavigate={onNavigate} />
        <main className="flex-1 overflow-y-auto">
          <div className="flex items-center gap-2 h-12 px-4 border-b border-border/50 glass-header sticky top-0 z-10">
            <SidebarTrigger className="text-sidebar-foreground hover:text-[#a93800]" />
            <div className="flex-1" />
          </div>
          <div className="p-6 lg:p-8">
            {children}
          </div>
        </main>
      </div>
    </SidebarProvider>
  )
}
