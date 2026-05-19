import { NextResponse } from "next/server";

const HERMES_SERVER = "http://127.0.0.1:8000";

/**
 * Proxy the Hermes session token from the web server's HTML.
 * The browser calls this to avoid CORS issues when fetching the token directly.
 */
export async function GET() {
  try {
    const html = await fetch(`${HERMES_SERVER}/`, {
      signal: AbortSignal.timeout(5_000),
    }).then((r) => r.text());

    const match = html.match(/__HERMES_SESSION_TOKEN__\s*=\s*"([^"]+)"/);
    const token = match?.[1] ?? null;

    return NextResponse.json({ token });
  } catch {
    return NextResponse.json({ token: null }, { status: 503 });
  }
}
