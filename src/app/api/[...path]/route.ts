import { NextRequest, NextResponse } from "next/server";

const HERMES_SERVER = "http://127.0.0.1:8000";

/**
 * Catch-all proxy for Hermes web server endpoints.
 *
 * Routes with specific files at src/app/api/* take precedence.
 * This handler catches everything else (e.g., /api/skills, /api/status, etc.)
 * and proxies requests to the Hermes FastAPI backend (:9119).
 */
async function handler(request: NextRequest): Promise<NextResponse> {
  const { pathname, search } = new URL(request.url);
  const targetUrl = `${HERMES_SERVER}${pathname}${search}`;

  try {
    const headers = new Headers(request.headers);
    // Remove host header (Next.js sets it to localhost:3000)
    headers.delete("host");

    // Forward the session token if present
    const token = request.headers.get("x-hermes-session-token");
    if (!token) {
      // Try to extract from referer or cookie (browser will have set it)
      headers.set("x-hermes-session-token", "");
    }

    const proxyResponse = await fetch(targetUrl, {
      method: request.method,
      headers,
      body: request.method !== "GET" && request.method !== "HEAD"
        ? await request.text().catch(() => null)
        : undefined,
    });

    const contentType = proxyResponse.headers.get("content-type") || "";
    const body = contentType.includes("application/json")
      ? await proxyResponse.json()
      : await proxyResponse.text();

    return NextResponse.json(body, {
      status: proxyResponse.status,
      headers: {
        "content-type": contentType || "application/json",
      },
    });
  } catch (err) {
    return NextResponse.json(
      { detail: `Backend unreachable: ${err instanceof Error ? err.message : "unknown"}` },
      { status: 503 },
    );
  }
}

export { handler as GET, handler as POST, handler as PUT, handler as DELETE, handler as PATCH };
