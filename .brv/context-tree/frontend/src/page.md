---
title: page
summary: ''
tags: []
related: []
keywords: []
createdAt: '2026-04-28T01:33:30.559Z'
updatedAt: '2026-04-28T01:33:30.559Z'
---
## Reason
Preserving complete src/app/page.tsx from hermes-dashboard project

## Raw Concept
**Task:**
Preserve src/app/page.tsx

**Files:**
- src/app/page.tsx

**Timestamp:** 2026-04-28

**Patterns:**
- `OverviewPage` - Component or function
- `SkillStudioPage` - Component or function
- `EvolutionPage` - Component or function
- `DatasetPage` - Component or function
- `MemoryPage` - Component or function
- `MetricsPage` - Component or function
- `LogsPage` - Component or function
- `SettingsPage` - Component or function
- `Home` - Component or function
- `PageComponent` - Component or function

## Narrative
### Structure
TSX file with 10 components/functions

### Highlights
Source: hermes-dashboard/src/app/page.tsx

---


&quot;use client&quot;;

import { useState } from &quot;react&quot;;
import Sidebar from &quot;@/components/Sidebar&quot;;
import dynamic from &quot;next/dynamic&quot;;
import type { Page } from &quot;@/components/Sidebar&quot;;

// Lazy load page components with loading states
const OverviewPage = dynamic(() =&gt; import(&quot;@/components/pages/OverviewPage&quot;), {
  loading: () =&gt; &lt;div className=&quot;min-h-[20rem] flex items-center justify-center&quot;&gt;Cargando Overview...&lt;/div&gt;,
});
const SkillStudioPage = dynamic(() =&gt; import(&quot;@/components/pages/SkillStudioPage&quot;), {
  loading: () =&gt; &lt;div className=&quot;min-h-[20rem] flex items-center justify-center&quot;&gt;Cargando Skill Studio...&lt;/div&gt;,
});
const EvolutionPage = dynamic(() =&gt; import(&quot;@/components/pages/EvolutionPage&quot;), {
  loading: () =&gt; &lt;div className=&quot;min-h-[20rem] flex items-center justify-center&quot;&gt;Cargando Evolution...&lt;/div&gt;,
});
const DatasetPage = dynamic(() =&gt; import(&quot;@/components/pages/DatasetPage&quot;), {
  loading: () =&gt; &lt;div className=&quot;min-h-[20rem] flex items-center justify-center&quot;&gt;Cargando Datasets...&lt;/div&gt;,
});
const MemoryPage = dynamic(() =&gt; import(&quot;@/components/pages/MemoryPage&quot;), {
  loading: () =&gt; &lt;div className=&quot;min-h-[20rem] flex items-center justify-center&quot;&gt;Cargando Memory...&lt;/div&gt;,
});
const MetricsPage = dynamic(() =&gt; import(&quot;@/components/pages/MetricsPage&quot;), {
  loading: () =&gt; &lt;div className=&quot;min-h-[20rem] flex items-center justify-center&quot;&gt;Cargando Metrics...&lt;/div&gt;,
});
const LogsPage = dynamic(() =&gt; import(&quot;@/components/pages/LogsPage&quot;), {
  loading: () =&gt; &lt;div className=&quot;min-h-[20rem] flex items-center justify-center&quot;&gt;Cargando Logs...&lt;/div&gt;,
});
const SettingsPage = dynamic(() =&gt; import(&quot;@/components/pages/SettingsPage&quot;), {
  loading: () =&gt; &lt;div className=&quot;min-h-[20rem] flex items-center justify-center&quot;&gt;Cargando Settings...&lt;/div&gt;,
});


const pages: Record&lt;Page, React.ComponentType&gt; = {
  overview: OverviewPage,
  skills: SkillStudioPage,
  evolution: EvolutionPage,
  datasets: DatasetPage,
  memory: MemoryPage,
  metrics: MetricsPage,
  logs: LogsPage,
  settings: SettingsPage,
};

export default function Home() {
  const [activePage, setActivePage] = useState&lt;Page&gt;(&quot;overview&quot;);
  const PageComponent = pages[activePage];

  return (
    &lt;div className=&quot;flex min-h-screen&quot;&gt;
      &lt;Sidebar activePage={activePage} onNavigate={setActivePage} /&gt;
      &lt;main className=&quot;flex-1 p-6 lg:p-8 overflow-y-auto&quot;&gt;
        &lt;PageComponent /&gt;
      &lt;/main&gt;
    &lt;/div&gt;
  );
}

    
