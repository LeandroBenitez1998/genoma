// ── Infrastructure: Resilient API client ──────────────────────────────
//
// Contract  → docs/api/hermes-api.openapi.yaml
// Design    → AbortController timeouts, typed errors, network detection
// Auth      → Hermes session-token (X-Hermes-Session-Token), auto-refresh on 401
// Proxy     → Next.js rewrites /api/* → Hermes web server (:9119)
// Fallback  → relative URLs (127.0.0.1 evita DNS roto en tiling WMs/Linux)
// Env       → NEXT_PUBLIC_API_BASE (solo para WebSocket y token fetch)

// ── Env resolution ───────────────────────────────────────────────────
function resolveBase(): string {
  // Hardcoded to FastAPI backend — env vars don't survive Turbopack HMR
  return "http://localhost:8000";
}

const API_BASE = resolveBase();

// URL absoluta del backend (para token fetch y WebSocket)
const HERMES_SERVER = API_BASE || "http://127.0.0.1:8000";

// ── Session token (Hermes auth) ──────────────────────────────────────
let _sessionToken: string | null = null;
let _tokenPromise: Promise<string | null> | null = null;

async function fetchSessionToken(): Promise<string | null> {
  try {
    const res = await fetch("/api/auth/token", {
      signal: AbortSignal.timeout(5_000),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data?.token ?? null;
  } catch {
    return null;
  }
}

async function getSessionToken(): Promise<string | null> {
  if (_sessionToken) return _sessionToken;
  if (!_tokenPromise) {
    _tokenPromise = fetchSessionToken().then((token) => {
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
export type ErrorKind = "network" | "timeout" | "server" | "client";

export class ApiError extends Error {
  readonly kind: ErrorKind;
  readonly status?: number;
  readonly endpoint: string;

  constructor(kind: ErrorKind, message: string, endpoint: string, status?: number) {
    super(message);
    this.name = "ApiError";
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
interface ApiOptions extends Omit<RequestInit, "signal"> {
  /** Timeout en ms. Default 15s. 0 = sin timeout. */
  timeout?: number;
}

async function executeRequest<T>(
  path: string,
  init: RequestInit & { timeout?: number },
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const controller = new AbortController();
  const timer =
    init.timeout && init.timeout > 0
      ? setTimeout(() => controller.abort(), init.timeout)
      : null;
  const signal = controller.signal;

  try {
    const res = await fetch(url, { ...init, signal });

    if (timer) clearTimeout(timer);

    if (!res.ok) {
      const body = await res.text().catch(() => res.statusText);
      const kind: ErrorKind = res.status >= 500 ? "server" : "client";
      throw new ApiError(kind, `HTTP ${res.status}: ${body.slice(0, 200)}`, path, res.status);
    }

    return res.json() as T;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

export async function api<T>(path: string, options?: ApiOptions): Promise<T> {
  const { timeout = DEFAULT_TIMEOUT_MS, ...init } = options ?? {};
  const token = await getSessionToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { "X-Hermes-Session-Token": token } : {}),
    ...((init.headers as Record<string, string>) ?? {}),
  };

  try {
    return await executeRequest<T>(path, { ...init, headers, timeout });
  } catch (err: unknown) {
    // Auto-refresh token on 401 and retry once
    if (err instanceof ApiError && err.status === 401) {
      invalidateToken();
      const freshToken = await getSessionToken();
      if (freshToken) {
        headers["X-Hermes-Session-Token"] = freshToken;
        return executeRequest<T>(path, { ...init, headers, timeout });
      }
    }

    // Re-lanzar errores ya tipados
    if (err instanceof ApiError) throw err;

    // AbortController / timeout
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError("timeout", `Request to ${path} timed out after ${timeout}ms`, path);
    }

    // TypeError (network unreachable, CORS, DNS)
    if (err instanceof TypeError) {
      throw new ApiError("network", `Cannot reach ${HERMES_SERVER} — ${err.message}`, path);
    }

    // Fallback
    throw new ApiError("network", err instanceof Error ? err.message : "Unknown fetch error", path);
  }
}

// ── WebSocket helper ─────────────────────────────────────────────────
let _wsToken: string | null = null;

export async function wsConnect(onMessage: (data: unknown) => void): Promise<WebSocket> {
  // Lazy-load token
  if (!_wsToken) {
    _wsToken = await getSessionToken();
  }
  const tokenQs = _wsToken ? `?token=${encodeURIComponent(_wsToken)}` : "";
  const wsUrl = HERMES_SERVER.replace(/^http/, "ws") + "/ws/stream" + tokenQs;
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      // ignore parse errors
    }
  };

  ws.onclose = () => {
    // Auto-reconnect after 3s
    setTimeout(() => wsConnect(onMessage), 3000);
  };

  return ws;
}

// ── Health check (for Circuit Breaker) ───────────────────────────────
//
// Uses /api/health which is public (no session token required), making it
// the ideal endpoint for connectivity checks.
export async function checkHealth(): Promise<{
  ok: boolean;
  kind?: ErrorKind;
  message?: string;
}> {
  try {
    await api<unknown>("/api/health", { timeout: 5_000 });
    return { ok: true };
  } catch (err) {
    if (err instanceof ApiError) {
      return { ok: false, kind: err.kind, message: err.message };
    }
    return { ok: false, kind: "network", message: "Unknown error" };
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
  frontmatter: Record<string, unknown>;
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
  splits: Record<string, number>;
  total: number;
}

export interface ConstraintResult {
  passed: boolean;
  constraint: string;
  message: string;
  details: string | null;
}

export const fetchSkills = () => api<SkillInfo[]>("/api/skills");
export const fetchSkill = (name: string) => api<SkillDetail>(`/api/skills/${name}`);
export const fetchSkillHistory = (name: string) =>
  api<EvolutionRun[]>(`/api/skills/${name}/evolution-history`);

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

export const fetchSkillProviders = () =>
  api<{ status: string; providers: ProviderSummary[] }>("/api/skills/providers");

export const toggleSkillEnabled = (provider: string, skillName: string, enabled: boolean) =>
  api<{ status: string; enabled: boolean }>("/api/skills/toggle", {
    method: "POST",
    body: JSON.stringify({ provider, skill_name: skillName, enabled }),
  });

export const deleteProviderSkill = (provider: string, skillName: string) =>
  api<{ status: string; message: string }>(`/api/skills/${provider}/${encodeURIComponent(skillName)}`, {
    method: "DELETE",
  });

export const deleteGlobalSkill = (skillName: string) =>
  api<{ status: string; message: string }>(`/api/skills/global/${encodeURIComponent(skillName)}`, {
    method: "DELETE",
  });

export const refreshSkills = () =>
  api<{ status: string; providers: ProviderSummary[] }>("/api/skills/refresh");
export const fetchEvolutionRuns = () => api<EvolutionRun[]>("/api/evolution/runs");

export interface SkillDiff {
  skill_name: string;
  run_dir: string;
  baseline: string | null;
  evolved: string | null;
  metrics: Record<string, unknown> | null;
}

export const fetchSkillDiff = (skillName: string, runDir: string) =>
  api<SkillDiff>(`/api/skills/${encodeURIComponent(skillName)}/evolution/${encodeURIComponent(runDir)}/diff`);

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

export const fetchJobs = (activeOnly = false) =>
  api<EvolutionJob[]>(`/api/jobs?active_only=${activeOnly}`);

export const fetchJob = (jobId: string) =>
  api<EvolutionJob>(`/api/jobs/${jobId}`);

export const fetchJobLogs = (jobId: string, since = 0) =>
  api<{ job_id: string; total_lines: number; logs: string[]; status: string; progress: number }>(
    `/api/jobs/${jobId}/logs?since=${since}`
  );

export const cancelJob = (jobId: string) =>
  api<{ status: string; job_id: string }>(`/api/jobs/${jobId}`, { method: "DELETE" });

export const startEvolution = (skillName: string, iterations: number) =>
  api<{ job_id: string; skill: string; status: string; error?: string }>("/api/evolution/start", {
    method: "POST",
    body: JSON.stringify({ skill_name: skillName, iterations, eval_source: "synthetic" }),
  });
export const fetchMetrics = () => api<MetricsData>("/api/metrics");
export const fetchDatasets = () => api<DatasetInfo[]>("/api/datasets");
export const fetchDataset = (skill: string) =>
  api<Record<string, unknown[]>>(`/api/datasets/${skill}`);
export const validateSkill = (name: string) =>
  api<ConstraintResult[]>(`/api/constraints/validate/${name}`);
export const fetchHealth = () =>
  api<{
    status: string;
    hermes_repo: string;
    hermes_repo_exists: boolean;
    evolution_dir: string;
    evolution_dir_exists: boolean;
    skills_count: number;
    categories: Record<string, number>;
  }>("/api/health");

// ── Curator API — Skill Lifecycle Management ──────────────────────

export interface CuratorStatus {
  status: string;
  last_run: { timestamp: string | null } | null;
  last_run_dir: string | null;
  stats: {
    active: number;
    stale: number;
    archived: number;
    total: number;
    pinned: number;
  };
  pinned_skills: string[];
  least_recently_used: Array<{
    name: string;
    last_used: string;
    use_count: number;
    view_count: number;
  }>;
}

export interface CuratorSkillUsage {
  name: string;
  state: "active" | "stale" | "archived" | "untracked";
  pinned: boolean;
  use_count: number;
  view_count: number;
  patch_count: number;
  last_used_at: string | null;
  last_viewed_at: string | null;
  last_patched_at: string | null;
  created_at: string | null;
  archived_at: string | null;
  agent_created: boolean;
}

export interface CuratorReport {
  id: string;
  timestamp: string;
  has_report: boolean;
  has_run_data: boolean;
  summary?: {
    skills_reviewed: number;
    archived: number;
    patched: number;
    consolidated: number;
  };
}

export interface CuratorReportDetail {
  id: string;
  timestamp: string;
  report_md?: string;
  run_data?: Record<string, unknown>;
}

export const fetchCuratorStatus = () =>
  api<CuratorStatus>("/api/curator/status");

export const fetchCuratorSkills = () =>
  api<{ skills: CuratorSkillUsage[] }>("/api/curator/skills");

export const curatorPin = (skill: string) =>
  api<{ status: string; pinned: boolean }>(`/api/curator/pin/${encodeURIComponent(skill)}`, { method: "POST" });

export const curatorUnpin = (skill: string) =>
  api<{ status: string; pinned: boolean }>(`/api/curator/unpin/${encodeURIComponent(skill)}`, { method: "POST" });

export const curatorRestore = (skill: string) =>
  api<{ status: string; restored: boolean }>(`/api/curator/restore/${encodeURIComponent(skill)}`, { method: "POST" });

export const curatorRun = (sync = false) =>
  api<{ status: string; report_id?: string; transitions?: Record<string, string[]> }>(
    `/api/curator/run?sync=${sync}`,
    { method: "POST" }
  );

export const fetchCuratorReports = (limit = 10) =>
  api<{ reports: CuratorReport[] }>(`/api/curator/reports?limit=${limit}`);

export const fetchCuratorReport = (reportId: string) =>
  api<CuratorReportDetail>(`/api/curator/reports/${reportId}`);
