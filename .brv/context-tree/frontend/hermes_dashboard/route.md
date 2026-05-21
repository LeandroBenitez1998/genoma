---
title: Route
summary: Source file app/api/auth/token/route.ts in the Next.js frontend
tags: []
related: [frontend/hermes_dashboard/hermes_dashboard_frontend.md, frontend/hermes_dashboard/architecture_overview.md, frontend/hermes_dashboard/layout.md, frontend/hermes_dashboard/page.md, frontend/hermes_dashboard/globals.md]
keywords: []
createdAt: '2026-05-21T07:39:26.003Z'
updatedAt: '2026-05-21T07:39:26.006Z'
---
## Reason
Curate app/api/auth/token/route.ts from src folder

## Raw Concept
**Task:**
Document app/api/auth/token/route.ts

**Timestamp:** 2026-05-21

## Narrative
### Structure
Implementation for app/api/auth/token/route.ts

### Highlights
Captured complete source content from app/api/auth/token/route.ts

---

import { NextRequest, NextResponse } from &quot;next/server&quot;;

const HERMES_SERVER = &quot;http://127.0.0.1:8000&quot;;

/**
 * Catch-all proxy for Hermes web server endpoints.
 *
 * Routes with specific files at src/app/api/* take precedence.
 * This handler catches everything else (e.g., /api/skills, /api/status, etc.)
 * and proxies requests to the Hermes FastAPI backend (:9119).
 */
async function handler(request: NextRequest): Promise&lt;NextResponse&gt; {
  const { pathname, search } = new URL(request.url);
  const targetUrl = `${HERMES_SERVER}${pathname}${search}`;

  try {
    const headers = new Headers(request.headers);
    // Remove host header (Next.js sets it to localhost:3000)
    headers.delete(&quot;host&quot;);

    // Forward the session token if present
    const token = request.headers.get(&quot;x-hermes-session-token&quot;);
    if (!token) {
      // Try to extract from referer or cookie (browser will have set it)
      headers.set(&quot;x-hermes-session-token&quot;, &quot;&quot;);
    }

    const proxyResponse = await fetch(targetUrl, {
      method: request.method,
      headers,
      body: request.method !== &quot;GET&quot; &amp;&amp; request.method !== &quot;HEAD&quot;
        ? await request.text().catch(() =&gt; null)
        : undefined,
    });

    const contentType = proxyResponse.headers.get(&quot;content-type&quot;) || &quot;&quot;;
    const body = contentType.includes(&quot;application/json&quot;)
      ? await proxyResponse.json()
      : await proxyResponse.text();

    return NextResponse.json(body, {
      status: proxyResponse.status,
      headers: {
        &quot;content-type&quot;: contentType || &quot;application/json&quot;,
      },
    });
  } catch (err) {
    return NextResponse.json(
      { detail: `Backend unreachable: ${err instanceof Error ? err.message : &quot;unknown&quot;}` },
      { status: 503 },
    );
  }
}

export { handler as GET, handler as POST, handler as PUT, handler as DELETE, handler as PATCH };

---


import { NextResponse } from &quot;next/server&quot;;

const HERMES_SERVER = &quot;http://127.0.0.1:8000&quot;;

/**
 * Proxy the Hermes session token from the web server&apos;s HTML.
 * The browser calls this to avoid CORS issues when fetching the token directly.
 */
export async function GET() {
  try {
    const html = await fetch(`${HERMES_SERVER}/`, {
      signal: AbortSignal.timeout(5_000),
    }).then((r) =&gt; r.text());

    const match = html.match(/__HERMES_SESSION_TOKEN__\s*=\s*&quot;([^&quot;]+)&quot;/);
    const token = match?.[1] ?? null;

    return NextResponse.json({ token });
  } catch {
    return NextResponse.json({ token: null }, { status: 503 });
  }
}

    
