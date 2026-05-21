---
title: Layout
summary: Source file app/layout.tsx in the Next.js frontend
tags: []
related: [frontend/hermes_dashboard/hermes_dashboard_frontend.md, frontend/hermes_dashboard/architecture_overview.md, frontend/hermes_dashboard/page.md, frontend/hermes_dashboard/globals.md, frontend/hermes_dashboard/route.md]
keywords: []
createdAt: '2026-05-21T07:39:26.010Z'
updatedAt: '2026-05-21T07:39:26.010Z'
---
## Reason
Curate app/layout.tsx from src folder

## Raw Concept
**Task:**
Document app/layout.tsx

**Timestamp:** 2026-05-21

## Narrative
### Structure
Implementation for app/layout.tsx

### Highlights
Captured complete source content from app/layout.tsx

---


import type { Metadata } from &quot;next&quot;;
import { Inter, Geist_Mono } from &quot;next/font/google&quot;;
import { TooltipProvider } from &quot;@/components/ui/tooltip&quot;;
import { ReactQueryProvider } from &apos;@/components/ReactQueryProvider&apos;;
import ThemeAwareBackground from &quot;@/components/ThemeAwareBackground&quot;;
import &quot;./globals.css&quot;;

const inter = Inter({
  variable: &quot;--font-inter&quot;,
  subsets: [&quot;latin&quot;],
  display: &quot;swap&quot;,
});

const geistMono = Geist_Mono({
  variable: &quot;--font-geist-mono&quot;,
  subsets: [&quot;latin&quot;],
});

export const metadata: Metadata = {
  title: &quot;Genoma — Agent-Agnostic Evolution Interface&quot;,
  description: &quot;Cross-agent evaluation &amp; evolution dashboard. Zero-friction setup.&quot;,
};

export default function RootLayout({
  children,
}: Readonly&lt;{
  children: React.ReactNode;
}&gt;) {
  return (
    &lt;html
      lang=&quot;en&quot;
      suppressHydrationWarning={true}
      className={`${inter.variable} ${geistMono.variable}`}
    &gt;
      &lt;head&gt;
        &lt;script
          dangerouslySetInnerHTML={{
            __html: `
              (function () {
                try {
                  var theme = localStorage.getItem(&apos;genoma-theme&apos;);
                  if (theme === &apos;dark&apos; || (!theme &amp;&amp; window.matchMedia(&apos;(prefers-color-scheme: dark)&apos;).matches)) {
                    document.documentElement.classList.add(&apos;dark&apos;);
                  } else {
                    document.documentElement.classList.remove(&apos;dark&apos;);
                  }
                } catch (_) {}
              })();
            `,
          }}
        /&gt;
      &lt;/head&gt;
      &lt;body className=&quot;min-h-screen bg-background text-foreground antialiased&quot;&gt;
        &lt;TooltipProvider delayDuration={200}&gt;
          &lt;ReactQueryProvider&gt;
            &lt;ThemeAwareBackground /&gt;
            {children}
          &lt;/ReactQueryProvider&gt;
        &lt;/TooltipProvider&gt;
      &lt;/body&gt;
    &lt;/html&gt;
  );
}

    
