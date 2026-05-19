"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import AppSidebar from "@/components/Sidebar";
import type { Page } from "@/components/Sidebar";
import { AnimatedThemeToggler } from "@/components/ui/animated-theme-toggler";

// Lazy load page components
const OverviewPage = dynamic(() => import("@/components/pages/OverviewPage"), {
  loading: () => <PageLoader label="Overview" />,
});
const SkillStudioPage = dynamic(() => import("@/components/pages/SkillStudioPage"), {
  loading: () => <PageLoader label="Skill Studio" />,
});
const EvolutionPage = dynamic(() => import("@/components/pages/EvolutionPage"), {
  loading: () => <PageLoader label="Evolution" />,
});
const DatasetPage = dynamic(() => import("@/components/pages/DatasetPage"), {
  loading: () => <PageLoader label="Datasets" />,
});
const MetricsPage = dynamic(() => import("@/components/pages/MetricsPage"), {
  loading: () => <PageLoader label="Metrics" />,
});
const LogsPage = dynamic(() => import("@/components/pages/LogsPage"), {
  loading: () => <PageLoader label="Logs" />,
});
const SettingsPage = dynamic(() => import("@/components/pages/SettingsPage"), {
  loading: () => <PageLoader label="Settings" />,
});
const CuratorPage = dynamic(() => import("@/components/pages/CuratorPage"), {
  loading: () => <PageLoader label="Curator" />,
});

function PageLoader({ label }: { label: string }) {
  return (
    <div className="min-h-[20rem] flex items-center justify-center">
      <p className="text-sm text-muted-foreground animate-pulse">
        Cargando {label}...
      </p>
    </div>
  );
}

const pages: Record<Page, React.ComponentType> = {
  overview: OverviewPage,
  skills: SkillStudioPage,
  evolution: EvolutionPage,
  datasets: DatasetPage,
  metrics: MetricsPage,
  logs: LogsPage,
  settings: SettingsPage,
  curator: CuratorPage,
};

export default function Home() {
  const [activePage, setActivePage] = useState<Page>("overview");
  const PageComponent = pages[activePage];

  return (
    <AppSidebar activePage={activePage} onNavigate={setActivePage}>
      {/* Fixed theme toggler — top right corner */}
      <AnimatedThemeToggler
        className="fixed top-4 right-4 z-50 p-2.5 rounded-full bg-card border border-border shadow-md hover:shadow-lg hover:bg-accent transition-all duration-200 text-foreground"
        duration={400}
      />
      <PageComponent />
    </AppSidebar>
  );
}
