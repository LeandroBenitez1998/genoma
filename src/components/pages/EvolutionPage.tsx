"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  GitBranch,
  Play,
  Square,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Minus,
  Dna,
  ChevronDown,
  ChevronRight,
  Activity,
  AlertCircle,
  Code2,
  FileText,
  X,
  RefreshCw,
  WifiOff,
  Zap,
  Sparkles,
} from "lucide-react";
import {
  fetchEvolutionRuns,
  fetchSkills,
  fetchJobs,
  fetchJobLogs,
  startEvolution,
  cancelJob,
  fetchSkillDiff,
  checkHealth,
  isApiError,
  api,
  type SkillDiff,
  type EvolutionRun,
  type SkillInfo,
  type EvolutionJob,
} from "@/lib/api";
import { ElectricBorder, ShinyText, SpotlightCard, ClickSpark } from "@/components/bits";
import DarkSelect from "@/components/bits/DarkSelect";
import SkillDiffViewer from "@/components/SkillDiffViewer";

// ── Provider config ────────────────────────────────────────────────
const PROVIDER_META: Record<string, { icon: string; color: string }> = {
  hermes: { icon: "🪽", color: "emerald" },
  "claude-code": { icon: "🤖", color: "violet" },
  opencode: { icon: "💻", color: "blue" },
  kilocode: { icon: "⚡", color: "amber" },
  antigravity: { icon: "🚀", color: "rose" },
};

interface EvolvableProvider {
  provider: string;
  total: number;
  enabled: number;
  skills: { name: string; description: string; enabled: boolean; category: string }[];
}

const STATUS_LABELS: Record<string, string> = {
  queued: "Queued",
  loading_skill: "Loading Skill",
  building_dataset: "Building Dataset",
  validating: "Validating",
  configuring: "Configuring",
  optimizing: "Optimizing",
  evaluating: "Evaluating",
  saving: "Saving",
  completed: "Completed",
  failed: "Failed",
};

type ConnectionState = "checking" | "connected" | "disconnected";

function ProgressBar({ progress, status }: { progress: number; status: string }) {
  const color =
    status === "failed"
      ? "bg-error"
      : status === "completed"
      ? "bg-success"
      : "bg-gradient-to-r from-accent-violet to-accent-cyan";

  return (
    <div className="h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
      <motion.div
        className={`h-full rounded-full ${color}`}
        initial={{ width: 0 }}
        animate={{ width: `${Math.max(progress * 100, 2)}%` }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        style={
          status !== "failed" && status !== "completed"
            ? { boxShadow: "0 0 8px rgba(139,92,246,0.5)" }
            : {}
        }
      />
    </div>
  );
}

function ActiveJobCard({
  job,
  onCancel,
}: {
  job: EvolutionJob;
  onCancel: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const [logs, setLogs] = useState<string[]>(job.logs || []);
  const logsRef = useRef<HTMLDivElement>(null);
  const logIndex = useRef(logs.length);

  useEffect(() => {
    if (job.status === "completed" || job.status === "failed") return;

    const interval = setInterval(async () => {
      try {
        const data = await fetchJobLogs(job.id, logIndex.current);
        if (data.logs?.length) {
          setLogs((prev) => [...prev, ...data.logs]);
          logIndex.current = data.total_lines;
        }
      } catch {}
    }, 1500);

    return () => clearInterval(interval);
  }, [job.id, job.status]);

  useEffect(() => {
    if (logsRef.current) logsRef.current.scrollTop = logsRef.current.scrollHeight;
  }, [logs]);

  const isActive = job.status !== "completed" && job.status !== "failed";

  return (
    <motion.div layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
      <ElectricBorder color={job.status === "failed" ? "#ef4444" : "#8b5cf6"} active={isActive} speed={1.5} borderRadius={16}>
        <div className="glass-card rounded-2xl overflow-hidden">
          <div className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isActive ? (
                <Loader2 className="w-3.5 h-3.5 text-accent-violet animate-spin" />
              ) : job.status === "completed" ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-success" />
              ) : (
                <XCircle className="w-3.5 h-3.5 text-error" />
              )}
              <div>
                <p className="text-sm font-semibold">{job.skill_name}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] font-mono text-muted-foreground">
                    {STATUS_LABELS[job.status] || job.status}
                  </span>
                  {isActive && job.status === "optimizing" && (
                    <span className="text-[10px] font-mono text-accent-violet">
                      iter {job.current_iteration}/{job.iterations}
                    </span>
                  )}
                  {job.pid && <span className="text-[10px] font-mono text-muted-foreground/50">pid:{job.pid}</span>}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {isActive && (
                <ShinyText text={STATUS_LABELS[job.status] || "Running"} speed={2} color="#8b5cf6" shineColor="#c4b5fd" className="text-xs font-bold" />
              )}
              {isActive && (
                <button onClick={() => onCancel(job.id)} className="p-1.5 rounded-lg bg-error/10 text-error hover:bg-error/20 transition-colors" title="Cancel">
                  <Square className="w-3 h-3" />
                </button>
              )}
              <button onClick={() => setExpanded(!expanded)} className="p-1.5 rounded-lg bg-white/[0.03] text-muted-foreground hover:text-foreground transition-colors">
                {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              </button>
            </div>
          </div>

          <div className="px-4 pb-2">
            <ProgressBar progress={job.progress} status={job.status} />
          </div>

          {/* Scores */}
          {(job.baseline_score !== null || job.evolved_score !== null || job.current_best_score !== null) && (
            <div className="px-4 pb-2 flex items-center gap-4 text-xs flex-wrap">
              {job.baseline_score !== null && (
                <span className="text-muted-foreground">Baseline: <span className="font-mono">{(job.baseline_score * 100).toFixed(0)}%</span></span>
              )}
              {job.evolved_score !== null && (
                <span className="text-accent-violet">Evolved: <span className="font-mono font-semibold">{(job.evolved_score * 100).toFixed(0)}%</span></span>
              )}
              {job.improvement !== null && job.improvement !== 0 && (
                <span className={job.improvement > 0 ? "text-success" : "text-error"}>
                  {job.improvement > 0 ? "+" : ""}{(job.improvement * 100).toFixed(1)}%
                </span>
              )}
              {job.current_best_score !== null && (
                <span className="text-accent-cyan">Best: <span className="font-mono">{(job.current_best_score * 100).toFixed(0)}%</span></span>
              )}
            </div>
          )}

          {/* Error */}
          {job.error && (
            <div className="px-4 pb-2">
              <div className="flex items-start gap-2 text-xs text-error bg-error/5 rounded-lg px-3 py-2">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                <span>{job.error}</span>
              </div>
            </div>
          )}

          {/* Logs */}
          <AnimatePresence>
            {expanded && (
              <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                <div ref={logsRef} className="mx-4 mb-4 rounded-xl bg-black/50 border border-white/[0.04] max-h-48 overflow-y-auto">
                  <div className="p-3 font-mono text-[10px] leading-relaxed">
                    {logs.length === 0 ? (
                      <p className="text-muted-foreground/40">Waiting for output...</p>
                    ) : (
                      logs.map((line, i) => {
                        const isPhase = /Loaded:|Building|Validating|Configuring|Running|Evaluating|Optimization/.test(line);
                        const isError = /✗|Error|error|FAILED|failed/.test(line);
                        const isSuccess = /✓|completed|Saved/.test(line);
                        return (
                          <div key={i} className={isError ? "text-error" : isSuccess ? "text-success" : isPhase ? "text-accent-cyan font-semibold" : "text-muted-foreground/70"}>
                            {line}
                          </div>
                        );
                      })
                    )}
                    {isActive && <span className="cursor-blink text-muted-foreground/30" />}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </ElectricBorder>
    </motion.div>
  );
}

// ── Circuit Breaker Banner ────────────────────────────────────────────
function DisconnectedBanner({ onRetry }: { onRetry: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-2xl p-6 border border-error/20 bg-error/[0.03]"
    >
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-error/10 flex items-center justify-center flex-shrink-0">
          <WifiOff className="w-5 h-5 text-error" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-foreground">Backend Unavailable</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Hermes gateway is not responding. The service may be starting up or was restarted.
          </p>
        </div>
        <ClickSpark sparkColor="#ef4444" sparkCount={8}>
          <button
            onClick={onRetry}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-error/10 text-error hover:bg-error/20 transition-colors text-sm font-medium"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </ClickSpark>
      </div>
    </motion.div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────
export default function EvolutionPage() {
  const [runs, setRuns] = useState<EvolutionRun[]>([]);
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [activeJobs, setActiveJobs] = useState<EvolutionJob[]>([]);
  const [selectedSkill, setSelectedSkill] = useState("");
  const [iterations, setIterations] = useState(3);
  const [launching, setLaunching] = useState(false);
  const [launchError, setLaunchError] = useState("");
  const [loading, setLoading] = useState(true);
  const [openDiff, setOpenDiff] = useState<{ skill: string; runDir: string } | null>(null);
  const [validating, setValidating] = useState<string | null>(null);
  const [validationResults, setValidationResults] = useState<Record<string, any>>({});

  // Multi-provider state
  const [evolvableProviders, setEvolvableProviders] = useState<EvolvableProvider[]>([]);
  const [providerFilter, setProviderFilter] = useState<string>("all");

  // Circuit Breaker state
  const [connection, setConnection] = useState<ConnectionState>("checking");
  const [connectionError, setConnectionError] = useState("");

  const verifyConnection = useCallback(async (): Promise<boolean> => {
    setConnection("checking");
    const result = await checkHealth();
    if (result.ok) {
      setConnection("connected");
      setConnectionError("");
      return true;
    }
    setConnection("disconnected");
    setConnectionError(result.message ?? "Cannot reach Hermes backend");
    return false;
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);

    const ok = await verifyConnection();
    if (!ok) {
      setLoading(false);
      return;
    }

    try {
      const [r, s, j, ep] = await Promise.all([
        fetchEvolutionRuns().catch((e) => {
          if (isApiError(e)) setConnectionError(`${e.kind}: ${e.message}`);
          return [] as EvolutionRun[];
        }),
        fetchSkills().catch((e) => {
          if (isApiError(e)) setConnectionError(`${e.kind}: ${e.message}`);
          return [] as SkillInfo[];
        }),
        fetchJobs(true).catch((e) => {
          if (isApiError(e)) setConnectionError(`${e.kind}: ${e.message}`);
          return [] as EvolutionJob[];
        }),
        api<{ status: string; providers: EvolvableProvider[] }>("/api/evolution/evolvable").catch(() => ({ status: "ok", providers: [] as EvolvableProvider[] })),
      ]);
      setRuns(r);
      setSkills(s);
      setActiveJobs(j);
      setEvolvableProviders(ep.providers || []);
    } catch (e) {
      if (e instanceof Error) setConnectionError(e.message);
    }
    setLoading(false);
  }, [verifyConnection]);

  // Initial load + connection verification
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Poll active jobs
  useEffect(() => {
    if (connection !== "connected") return;
    const interval = setInterval(() => {
      fetchJobs(true).then(setActiveJobs).catch(() => {});
    }, 2000);
    return () => clearInterval(interval);
  }, [connection]);

  const handleStart = async () => {
    if (!selectedSkill) {
      setLaunchError("Please select a skill first");
      return;
    }
    if (iterations < 1 || iterations > 20) {
      setLaunchError("Iterations must be between 1 and 20");
      return;
    }

    setLaunching(true);
    setLaunchError("");

    try {
      const result = await startEvolution(selectedSkill, iterations);

      if (result.error) {
        setLaunchError(result.error);
      } else {
        const jobs = await fetchJobs(true);
        setActiveJobs(jobs);
        setSelectedSkill("");
      }
    } catch (e: unknown) {
      if (isApiError(e)) {
        setLaunchError(`${e.kind}: ${e.message}`);
        // Circuit breaker: mark disconnected on network errors
        if (e.kind === "network" || e.kind === "timeout") {
          setConnection("disconnected");
        }
      } else {
        setLaunchError(e instanceof Error ? e.message : "Failed to start evolution");
      }
    }

    setLaunching(false);
  };

  const handleCancel = async (jobId: string) => {
    try {
      await cancelJob(jobId);
      setActiveJobs((prev) => prev.filter((j) => j.id !== jobId));
    } catch {}
  };

  const handleValidate = async (skillName: string) => {
    setValidating(skillName);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/api/evolution/validate?skill_name=${skillName}`, { method: "POST" });
      const data = await res.json();
      setValidationResults(prev => ({ ...prev, [skillName]: data }));
    } catch (e) {
      setValidationResults(prev => ({ ...prev, [skillName]: { final_verdict: "ERROR", error: String(e) } }));
    }
    setValidating(null);
  };

  const handleRetry = async () => {
    await loadData();
  };

  const runsBySkill = runs.reduce((acc, run) => {
    (acc[run.skill_name] = acc[run.skill_name] || []).push(run);
    return acc;
  }, {} as Record<string, EvolutionRun[]>);

  return (
    <div className="space-y-6">
      {/* Circuit Breaker — Disconnected banner */}
      {connection === "disconnected" && <DisconnectedBanner onRetry={handleRetry} />}

      {/* Active Evolutions */}
      {connection === "connected" && activeJobs.length > 0 && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-accent-violet" />
            Active Evolutions
            <span className="text-[10px] font-mono text-accent-violet bg-accent-violet/10 px-2 py-0.5 rounded-full">{activeJobs.length}</span>
          </h2>
          <AnimatePresence>
            {activeJobs.map((job) => (
              <ActiveJobCard key={job.id} job={job} onCancel={handleCancel} />
            ))}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Launch Panel */}
      {connection !== "disconnected" && (
        <ElectricBorder color="#8b5cf6" active={launching} speed={1.5} borderRadius={16}>
          <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="glass-card rounded-2xl p-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2 mb-4">
              <Zap className="w-4 h-4 text-accent-violet" />
              Evolution Hub
              {evolvableProviders.length > 0 && (
                <span className="text-[10px] font-mono text-accent-violet bg-accent-violet/10 px-2 py-0.5 rounded-full ml-auto">
                  {evolvableProviders.reduce((acc, p) => acc + p.skills.length, 0)} skills · {evolvableProviders.length} providers
                </span>
              )}
            </h2>

            {/* Provider filter tabs */}
            {evolvableProviders.length > 0 && (
              <div className="flex gap-2 flex-wrap mb-4">
                <button
                  onClick={() => setProviderFilter("all")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    providerFilter === "all"
                      ? "bg-white/10 text-white border border-white/20"
                      : "bg-white/[0.03] text-muted-foreground border border-transparent hover:border-white/10"
                  }`}
                >
                  All
                </button>
                {evolvableProviders.map((p) => {
                  const meta = PROVIDER_META[p.provider] ?? { icon: "🔧", color: "" };
                  return (
                    <button
                      key={p.provider}
                      onClick={() => setProviderFilter(p.provider)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                        providerFilter === p.provider
                          ? "bg-accent-violet/10 text-accent-violet border border-accent-violet/20"
                          : "bg-white/[0.03] text-muted-foreground border border-transparent hover:border-white/10"
                      }`}
                    >
                      <span>{meta.icon}</span>
                      <span className="capitalize">{p.provider}</span>
                      <span className="text-[10px] opacity-50">({p.skills.length})</span>
                    </button>
                  );
                })}
              </div>
            )}

            <div className="flex flex-wrap items-end gap-4">
              <div className="flex-1 min-w-[200px]">
                <label className="text-xs text-muted-foreground mb-1 block">Skill</label>
                {loading || connection === "checking" ? (
                  <div className="px-4 py-2.5 rounded-xl bg-[#1a1a1a] border border-white/[0.08] text-sm text-muted-foreground animate-pulse">
                    {connection === "checking" ? "Checking connection..." : "Loading skills..."}
                  </div>
                ) : skills.length === 0 ? (
                  <div className="px-4 py-2.5 rounded-xl bg-[#1a1a1a] border border-white/[0.08] text-sm text-error flex items-center gap-2">
                    <AlertCircle className="w-3.5 h-3.5" />
                    No skills found — check backend connection
                  </div>
                ) : (
                <DarkSelect
                  value={selectedSkill}
                  onChange={setSelectedSkill}
                  placeholder="Select a skill..."
                  options={skills.map((s) => ({
                    value: s.name,
                    label: `${s.name} (${s.provider_count} provider${s.provider_count > 1 ? "s" : ""})`,
                  }))}
                />
                )}
              </div>

              <div className="w-32">
                <label className="text-xs text-muted-foreground mb-1 block">Iterations</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={iterations}
                  onChange={(e) => {
                    const v = parseInt(e.target.value);
                    if (!isNaN(v) && v >= 1 && v <= 20) setIterations(v);
                  }}
                  className="w-full px-4 py-2.5 rounded-xl bg-[#1a1a1a] border border-white/[0.08] text-sm text-foreground focus:outline-none focus:border-accent-violet/50"
                />
                <p className="text-[10px] text-muted-foreground mt-1">Current: {iterations}</p>
              </div>

              <ClickSpark sparkColor="#8b5cf6" sparkCount={10}>
                <button
                  onClick={handleStart}
                  disabled={!selectedSkill || launching}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-accent-violet text-white text-sm font-medium hover:bg-accent-violet/90 transition-colors disabled:opacity-40"
                >
                  {launching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  {launching ? "Starting..." : `Evolve (${iterations} iter${iterations > 1 ? "s" : ""})`}
                </button>
              </ClickSpark>
            </div>

            {launchError && (
              <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} className="mt-3 flex items-start gap-2 text-xs text-error bg-error/5 rounded-lg px-3 py-2">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                <span>{launchError}</span>
              </motion.div>
            )}
          </motion.div>
        </ElectricBorder>
      )}

      {/* Evolution History */}
      {connection !== "disconnected" && (
        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card rounded-2xl p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2 mb-4">
            <GitBranch className="w-4 h-4 text-accent-cyan" />
            Evolution History
          </h2>

          {connection === "checking" && (
            <p className="text-sm text-muted-foreground py-8 text-center">Checking connection...</p>
          )}
          {!loading && connection === "connected" && Object.keys(runsBySkill).length === 0 && (
            <p className="text-sm text-muted-foreground py-8 text-center">No evolution runs yet.</p>
          )}
          {Object.keys(runsBySkill).length > 0 && (
            <div className="space-y-6">
              {Object.entries(runsBySkill).map(([skillName, skillRuns]) => (
                <div key={skillName}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-3 h-3 rounded-full bg-accent-violet" />
                    <span className="text-sm font-semibold">{skillName}</span>
                    <span className="text-[10px] text-muted-foreground font-mono">{skillRuns.length} run{skillRuns.length > 1 ? "s" : ""}</span>
                    {/* Validation badge */}
                    {validationResults[skillName] && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                        validationResults[skillName].final_verdict?.includes("PASS") ? "bg-success/10 text-success" :
                        validationResults[skillName].final_verdict?.includes("MIXED") ? "bg-accent-cyan/10 text-accent-cyan" :
                        "bg-error/10 text-error"
                      }`}>
                        {validationResults[skillName].final_verdict}
                      </span>
                    )}
                    <button
                      onClick={() => handleValidate(skillName)}
                      disabled={validating === skillName}
                      className="text-[10px] px-2 py-0.5 rounded-lg bg-accent-violet/10 text-accent-violet hover:bg-accent-violet/20 transition-colors disabled:opacity-50"
                    >
                      {validating === skillName ? "..." : "Validate"}
                    </button>
                  </div>
                  <div className="ml-6 border-l border-white/[0.08] pl-6 space-y-3">
                    {skillRuns.map((run, i) => {
                      const improved = (run.improvement ?? 0) > 0;
                      const regressed = (run.improvement ?? 0) < 0;
                      return (
                        <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}>
                          <SpotlightCard
                            spotlightColor={improved ? "rgba(34,197,94,0.08)" : regressed ? "rgba(239,68,68,0.08)" : "rgba(255,255,255,0.03)"}
                            className="relative flex items-start gap-4 p-4 rounded-xl border border-white/[0.04]"
                          >
                            <div className="absolute -left-[31px] top-5 w-2 h-2 rounded-full bg-white/20" />
                            {run.constraints_passed ? <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0 mt-0.5" /> : <XCircle className="w-4 h-4 text-error flex-shrink-0 mt-0.5" />}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-mono text-muted-foreground">{run.timestamp}</span>
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.05] text-muted-foreground">{run.iterations} iters</span>
                              </div>
                              <div className="flex items-center gap-3 mt-2">
                                <div className="text-sm">
                                  <span className="text-muted-foreground font-mono">{(run.baseline_score * 100).toFixed(0)}%</span>
                                  <span className="text-muted-foreground mx-2">→</span>
                                  <span className={`font-mono font-semibold ${improved ? "text-success" : regressed ? "text-error" : "text-muted-foreground"}`}>
                                    {(run.evolved_score * 100).toFixed(0)}%
                                  </span>
                                </div>
                                {improved ? <TrendingUp className="w-3.5 h-3.5 text-success" /> : regressed ? <TrendingDown className="w-3.5 h-3.5 text-error" /> : <Minus className="w-3.5 h-3.5 text-muted-foreground" />}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                                <Clock className="w-3 h-3" />
                                {run.elapsed_seconds?.toFixed(0)}s
                              </div>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (openDiff?.skill === skillName && openDiff?.runDir === run.timestamp) {
                                    setOpenDiff(null);
                                  } else {
                                    setOpenDiff({ skill: skillName, runDir: run.timestamp });
                                  }
                                }}
                                className={`text-[10px] px-2 py-0.5 rounded-lg transition-colors border ${
                                  openDiff?.skill === skillName && openDiff?.runDir === run.timestamp
                                    ? "bg-accent-violet/10 text-accent-violet border-accent-violet/20"
                                    : "bg-white/[0.03] text-muted-foreground hover:text-foreground hover:bg-white/[0.08] border-white/[0.06]"
                                }`}
                              >
                                <GitBranch className="w-3 h-3 inline mr-0.5" />
                                {openDiff?.skill === skillName && openDiff?.runDir === run.timestamp ? "Close" : "Diff"}
                              </button>
                            </div>
                          </SpotlightCard>
                          {openDiff?.skill === skillName && openDiff?.runDir === run.timestamp && (
                            <SkillDiffViewer
                              skillName={skillName}
                              runDir={run.timestamp}
                              onClose={() => setOpenDiff(null)}
                            />
                          )}
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
