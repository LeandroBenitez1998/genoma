---
title: API Client Library
summary: TypeScript API client with typed functions for jobs, skills, evolution, and WebSocket connection management
tags: []
related: []
keywords: []
createdAt: '2026-04-28T03:46:41.151Z'
updatedAt: '2026-04-28T03:46:41.151Z'
---
## Reason
Preserving complete frontend API client with typed endpoints

## Raw Concept
**Task:**
Document frontend API client library

**Files:**
- src/lib/api.ts

**Timestamp:** 2026-04-28

## Narrative
### Structure
React Query-based API client with typed endpoints, WebSocket hooks, and API configuration

---


// ── Infrastructure: Resilient API client ──────────────────────────────
//
// Contract  → docs/api/hermes-api.openapi.yaml
// Design    → AbortController timeouts, typed errors, network detection
// Auth      → Hermes session-token (X-Hermes-Session-Token), auto-refresh on 401
// Fallback  → 127.0.0.1 (evita resolución DNS rota en tiling WMs/Linux)
// Env       → NEXT_PUBLIC_API_BASE (sin trailing slash)

// ── Env resolution ───────────────────────────────────────────────────
function resolveBase(): string {
  if (typeof window !== &quot;undefined&quot;) {
    // Client-side: NEXT_PUBLIC_ variables están expuestas
    const env = process.env as Record&lt;string, string | undefined&gt;;
    // Soporta ambas variables: NEXT_PUBLIC_API_BASE (nuevo estándar) y NEXT_PUBLIC_API_URL (legacy)
    const fromEnv = env.NEXT_PUBLIC_API_BASE ?? env.NEXT_PUBLIC_API_URL;
    if (fromEnv) return fromEnv.replace(/\/+$/, &quot;&quot;);
  }
  // Fallback: 127.0.0.1 en vez de localhost para evitar problemas DNS. Puerto 9119 = default de Hermes web.
  return &quot;http://127.0.0.1:9119&quot;;
}

const API_BASE = resolveBase();

// ── Session token (Hermes auth) ──────────────────────────────────────
let _sessionToken: string | null = null;
let _tokenPromise: Promise&lt;string | null&gt; | null = null;

async function fetchSessionToken(): Promise&lt;string | null&gt; {
  try {
    const html = await fetch(`${API_BASE}/`, {
      signal: AbortSignal.timeout(5_000),
    }).then((r) =&gt; r.text());
    const match = html.match(/__HERMES_SESSION_TOKEN__\s*=\s*&quot;([^&quot;]+)&quot;/);
    return match?.[1] ?? null;
  } catch {
    return null;
  }
}

async function getSessionToken(): Promise&lt;string | null&gt; {
  if (_sessionToken) return _sessionToken;
  if (!_tokenPromise) {
    _tokenPromise = fetchSessionToken().then((token) =&gt; {
      _sessionToken = token;
      _tokenPromise = null;
      return token;
    });
  }
  return _tokenPromise;
}

function invalidateToken(): void {
  _sessionToken = null;
  _tokenPromise = null;
}

// ── Defaults ─────────────────────────────────────────────────────────
const DEFAULT_TIMEOUT_MS = 15_000;

// ── Typed errors (contract: ApiError schema) ─────────────────────────
export type ErrorKind = &quot;network&quot; | &quot;timeout&quot; | &quot;server&quot; | &quot;client&quot;;

export class ApiError extends Error {
  readonly kind: ErrorKind;
  readonly status?: number;
  readonly endpoint: string;

  constructor(kind: ErrorKind, message: string, endpoint: string, status?: number) {
    super(message);
    this.name = &quot;ApiError&quot;;
    this.kind = kind;
    this.status = status;
    this.endpoint = endpoint;
  }
}

/** Type guard para distinguir errores de API de excepciones genéricas */
export function isApiError(err: unknown): err is ApiError {
  return err instanceof ApiError;
}

// ── Core fetch wrapper ───────────────────────────────────────────────
interface ApiOptions extends Omit&lt;RequestInit, &quot;signal&quot;&gt; {
  /** Timeout en ms. Default 15s. 0 = sin timeout. */
  timeout?: number;
}

async function executeRequest&lt;T&gt;(
  path: string,
  init: RequestInit &amp; { timeout?: number },
): Promise&lt;T&gt; {
  const url = `${API_BASE}${path}`;
  const controller = new AbortController();
  const timer =
    init.timeout &amp;&amp; init.timeout &gt; 0
      ? setTimeout(() =&gt; controller.abort(), init.timeout)
      : null;
  const signal = controller.signal;

  try {
    const res = await fetch(url, { ...init, signal });

    if (timer) clearTimeout(timer);

    if (!res.ok) {
      const body = await res.text().catch(() =&gt; res.statusText);
      const kind: ErrorKind = res.status &gt;= 500 ? &quot;server&quot; : &quot;client&quot;;
      throw new ApiError(kind, `HTTP ${res.status}: ${body.slice(0, 200)}`, path, res.status);
    }

    return res.json() as T;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

export async function api&lt;T&gt;(path: string, options?: ApiOptions): Promise&lt;T&gt; {
  const { timeout = DEFAULT_TIMEOUT_MS, ...init } = options ?? {};
  const token = await getSessionToken();

  const headers: Record&lt;string, string&gt; = {
    &quot;Content-Type&quot;: &quot;application/json&quot;,
    ...(token ? { &quot;X-Hermes-Session-Token&quot;: token } : {}),
    ...((init.headers as Record&lt;string, string&gt;) ?? {}),
  };

  try {
    return await executeRequest&lt;T&gt;(path, { ...init, headers, timeout });
  } catch (err: unknown) {
    // Auto-refresh token on 401 and retry once
    if (err instanceof ApiError &amp;&amp; err.status === 401) {
      invalidateToken();
      const freshToken = await getSessionToken();
      if (freshToken) {
        headers[&quot;X-Hermes-Session-Token&quot;] = freshToken;
        return executeRequest&lt;T&gt;(path, { ...init, headers, timeout });
      }
    }

    // Re-lanzar errores ya tipados
    if (err instanceof ApiError) throw err;

    // AbortController / timeout
    if (err instanceof DOMException &amp;&amp; err.name === &quot;AbortError&quot;) {
      throw new ApiError(&quot;timeout&quot;, `Request to ${path} timed out after ${timeout}ms`, path);
    }

    // TypeError (network unreachable, CORS, DNS)
    if (err instanceof TypeError) {
      throw new ApiError(&quot;network&quot;, `Cannot reach ${API_BASE} — ${err.message}`, path);
    }

    // Fallback
    throw new ApiError(&quot;network&quot;, err instanceof Error ? err.message : &quot;Unknown fetch error&quot;, path);
  }
}

// ── WebSocket helper ─────────────────────────────────────────────────
let _wsToken: string | null = null;

export async function wsConnect(onMessage: (data: unknown) =&gt; void): Promise&lt;WebSocket&gt; {
  // Lazy-load token
  if (!_wsToken) {
    _wsToken = await getSessionToken();
  }
  const tokenQs = _wsToken ? `?token=${encodeURIComponent(_wsToken)}` : &quot;&quot;;
  const wsUrl = API_BASE.replace(/^http/, &quot;ws&quot;) + &quot;/ws/stream&quot; + tokenQs;
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (event) =&gt; {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      // ignore parse errors
    }
  };

  ws.onclose = () =&gt; {
    // Auto-reconnect after 3s
    setTimeout(() =&gt; wsConnect(onMessage), 3000);
  };

  return ws;
}

// ── Health check (for Circuit Breaker) ───────────────────────────────
//
// Uses /api/status which is public (no session token required), making it
// the ideal endpoint for connectivity checks.
export async function checkHealth(): Promise&lt;{
  ok: boolean;
  kind?: ErrorKind;
  message?: string;
}&gt; {
  try {
    await api&lt;unknown&gt;(&quot;/api/status&quot;, { timeout: 5_000 });
    return { ok: true };
  } catch (err) {
    if (err instanceof ApiError) {
      return { ok: false, kind: err.kind, message: err.message };
    }
    return { ok: false, kind: &quot;network&quot;, message: &quot;Unknown error&quot; };
  }
}

// ── Typed API calls ──────────────────────────────────────────────────

export interface SkillInfo {
  name: string;
  path: string;
  description: string;
  size: number;
  last_modified: string;
  providers: string[];
  provider_count: number;
  category: string;
}

export interface SkillDetail {
  name: string;
  path: string;
  frontmatter: Record&lt;string, unknown&gt;;
  body: string;
  raw: string;
  size: number;
}

export interface EvolutionRun {
  skill_name: string;
  timestamp: string;
  baseline_score: number;
  evolved_score: number;
  improvement: number;
  elapsed_seconds: number;
  constraints_passed: boolean;
  iterations: number;
  optimizer_model: string;
}

export interface MetricsData {
  total_runs: number;
  skills_evolved: number;
  avg_improvement: number;
  best_improvement: number;
  total_time_seconds: number;
  avg_time_seconds: number;
  success_rate: number;
  runs: EvolutionRun[];
}

export interface DatasetInfo {
  skill: string;
  path: string;
  splits: Record&lt;string, number&gt;;
  total: number;
}

export interface ConstraintResult {
  passed: boolean;
  constraint: string;
  message: string;
  details: string | null;
}

export const fetchSkills = () =&gt; api&lt;SkillInfo[]&gt;(&quot;/api/skills&quot;);
export const fetchSkill = (name: string) =&gt; api&lt;SkillDetail&gt;(`/api/skills/${name}`);
export const fetchSkillHistory = (name: string) =&gt;
  api&lt;EvolutionRun[]&gt;(`/api/skills/${name}/evolution-history`);

// Skill management helpers
export interface ProviderSummary {
  name: string;
  total: number;
  enabled: number;
  skills: {
    name: string;
    description: string;
    enabled: boolean;
    tags: string[];
    is_fork?: boolean;
    category: string;
  }[];
}

export const fetchSkillProviders = () =&gt;
  api&lt;{ status: string; providers: ProviderSummary[] }&gt;(&quot;/api/skills/providers&quot;);

export const toggleSkillEnabled = (provider: string, skillName: string, enabled: boolean) =&gt;
  api&lt;{ status: string; enabled: boolean }&gt;(&quot;/api/skills/toggle&quot;, {
    method: &quot;POST&quot;,
    body: JSON.stringify({ provider, skill_name: skillName, enabled }),
  });

export const deleteProviderSkill = (provider: string, skillName: string) =&gt;
  api&lt;{ status: string; message: string }&gt;(`/api/skills/${provider}/${encodeURIComponent(skillName)}`, {
    method: &quot;DELETE&quot;,
  });

export const deleteGlobalSkill = (skillName: string) =&gt;
  api&lt;{ status: string; message: string }&gt;(`/api/skills/global/${encodeURIComponent(skillName)}`, {
    method: &quot;DELETE&quot;,
  });

export const refreshSkills = () =&gt;
  api&lt;{ status: string; providers: ProviderSummary[] }&gt;(&quot;/api/skills/refresh&quot;);
export const fetchEvolutionRuns = () =&gt; api&lt;EvolutionRun[]&gt;(&quot;/api/evolution/runs&quot;);

export interface SkillDiff {
  skill_name: string;
  run_dir: string;
  baseline: string | null;
  evolved: string | null;
  metrics: Record&lt;string, unknown&gt; | null;
}

export const fetchSkillDiff = (skillName: string, runDir: string) =&gt;
  api&lt;SkillDiff&gt;(`/api/skills/${encodeURIComponent(skillName)}/evolution/${encodeURIComponent(runDir)}/diff`);

// ── Job tracking ─────────────────────────────────────────────────────

export interface EvolutionJob {
  id: string;
  skill_name: string;
  status: string;
  iterations: number;
  current_iteration: number;
  pid: number | null;
  started_at: string;
  completed_at: string;
  baseline_score: number | null;
  current_best_score: number | null;
  evolved_score: number | null;
  improvement: number | null;
  error: string;
  progress: number;
  logs: string[];
}

export const fetchJobs = (activeOnly = false) =&gt;
  api&lt;EvolutionJob[]&gt;(`/api/jobs?active_only=${activeOnly}`);

export const fetchJob = (jobId: string) =&gt;
  api&lt;EvolutionJob&gt;(`/api/jobs/${jobId}`);

export const fetchJobLogs = (jobId: string, since = 0) =&gt;
  api&lt;{ job_id: string; total_lines: number; logs: string[]; status: string; progress: number }&gt;(
    `/api/jobs/${jobId}/logs?since=${since}`
  );

export const cancelJob = (jobId: string) =&gt;
  api&lt;{ status: string; job_id: string }&gt;(`/api/jobs/${jobId}`, { method: &quot;DELETE&quot; });

export const startEvolution = (skillName: string, iterations: number) =&gt;
  api&lt;{ job_id: string; skill: string; status: string; error?: string }&gt;(&quot;/api/evolution/start&quot;, {
    method: &quot;POST&quot;,
    body: JSON.stringify({ skill_name: skillName, iterations, eval_source: &quot;synthetic&quot; }),
  });
export const fetchMetrics = () =&gt; api&lt;MetricsData&gt;(&quot;/api/metrics&quot;);
export const fetchDatasets = () =&gt; api&lt;DatasetInfo[]&gt;(&quot;/api/datasets&quot;);
export const fetchDataset = (skill: string) =&gt;
  api&lt;Record&lt;string, unknown[]&gt;&gt;(`/api/datasets/${skill}`);
export const validateSkill = (name: string) =&gt;
  api&lt;ConstraintResult[]&gt;(`/api/constraints/validate/${name}`);
export const fetchHealth = () =&gt;
  api&lt;{
    status: string;
    hermes_repo: string;
    hermes_repo_exists: boolean;
    evolution_dir: string;
    evolution_dir_exists: boolean;
    skills_count: number;
    categories: Record&lt;string, number&gt;;
  }&gt;(&quot;/api/health&quot;);

    
