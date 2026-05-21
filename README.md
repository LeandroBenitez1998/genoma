# 🧬 Genoma

<div align="center">
  <img src="./genoma_logo.png" alt="Genoma Logo" width="200" />
</div>

Agent-agnostic evolution dashboard for AI coding agents.

---

## 🚀 Installation

### NPM CLI (Recommended)

```bash
npx genoma@latest serve
```

Starts backend (:8000) + frontend (:3000) + MCP server. Requires Node.js 18+, Python 3.10+, and `ANTHROPIC_API_KEY`.

### Local Development

```bash
./run.sh
```

Starts backend + frontend + MCP in parallel.

### Manual Setup

```bash
# Terminal 1: Backend
python3 -m pip install fastapi uvicorn pydantic python-dotenv --break-system-packages -q
python3 -m uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend
pnpm install --ignore-scripts
pnpm dev
```

