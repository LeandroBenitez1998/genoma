<!-- BEGIN:vinext-rules -->
# Migrated from Next.js to vinext (Vite-based)

This project uses [vinext](https://github.com/cloudflare/vinext) — a Vite plugin that reimplements the Next.js API surface. 
All `next/*` imports resolve through vinext shims. The frontend is a pure SPA served by Vite.

- `pnpm dev` → `vinext dev` (Vite dev server on :3000)
- `pnpm build` → `vinext build` (production bundle)
- `pnpm start` → `vinext start` (production server)
- API calls are proxied `/api/*` → FastAPI backend on :8000
- No webpack/Turbopack config — use Vite plugins instead
<!-- END:vinext-rules -->
