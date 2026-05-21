---
confidence: 0.97
sources: [frontend/_index.md, frontend/_index.md, docs/_index.md, backend/_index.md]
synthesized_at: '2026-05-21T07:43:50.188Z'
type: synthesis
title: Session-token proxying is the frontend/backend bridge
summary: The dashboard proxies API traffic through Next.js while the frontend client also speaks to the backend with Hermes session tokens, creating a layered auth/transport bridge.
tags: [frontend, backend, api, auth, websocket]
related: []
keywords: [session token, proxy, fastapi, nextjs, api client, '503', websocket, auth, transport]
createdAt: '2026-05-21T07:43:50.188Z'
updatedAt: '2026-05-21T07:43:50.188Z'
---

# Session-token proxying is the frontend/backend bridge

The frontend and backend share a transport pattern where Next.js routes proxy requests to the FastAPI server, forward the `x-hermes-session-token`, and the typed API client uses the same session-token mechanism for authenticated calls and reconnect behavior.

## Evidence

- **frontend**: The Next.js catch-all route proxies `/api/*` to `http://127.0.0.1:8000`, strips `host`, forwards `x-hermes-session-token`, and returns `503` when the backend is unreachable.
- **frontend**: `src/lib/api.ts` is a typed frontend API client authenticated with `X-Hermes-Session-Token`, includes AbortController timeouts, one-time refresh on `401`, and WebSocket auto-reconnect after 3s.
- **docs**: The API contract treats `NEXT_PUBLIC_API_BASE` as an override, standardizes `ApiError`, and maps `503` to a disconnected state for frontend UX.
- **backend**: The backend exposes REST endpoints plus WebSocket support for skills, evolution, jobs, datasets, graph output, and health checks.
