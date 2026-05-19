"use client";

import { useState, useEffect, useCallback } from "react";
import { api, startEvolution, fetchJobs, fetchJob, fetchSkillDiff, fetchEvolutionRuns } from "@/lib/api";
import type { EvolutionJob, EvolutionRun, SkillDiff } from "@/lib/api";
import {
  Zap, TrendingUp, GitCompare, History, Loader2, Play,
  CheckCircle2, XCircle, Clock, Sparkles, AlertTriangle,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────
interface EvolvableSkill {
  name: string;
  description: string;
  enabled: boolean;
  tags: string[];
  is_fork?: boolean;
  category: string;
}

interface EvolvableProvider {
  provider: string;
  total: number;
  enabled: number;
  skills: EvolvableSkill[];
}

interface EvolvableResponse {
  status: string;
  providers: EvolvableProvider[];
}

// ── Provider config ────────────────────────────────────────────────
const PROVIDER_META: Record<string, { icon: string; color: string; label: string }> = {
  hermes: { icon: "🪽", color: "emerald", label: "Hermes" },
  "claude-code": { icon: "🤖", color: "violet", label: "Claude Code" },
  opencode: { icon: "💻", color: "blue", label: "OpenCode" },
  kilocode: { icon: "⚡", color: "amber", label: "Kilocode" },
  antigravity: { icon: "🚀", color: "rose", label: "Antigravity" },
};

const COLOR_MAP: Record<string, string> = {
  emerald: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
  violet: "bg-violet-500/10 border-violet-500/30 text-violet-400",
  blue: "bg-blue-500/10 border-blue-500/30 text-blue-400",
  amber: "bg-amber-500/10 border-amber-500/30 text-amber-400",
  rose: "bg-rose-500/10 border-rose-500/30 text-rose-400",
};

// ── Sub-components ─────────────────────────────────────────────────

function ProviderTabs({
  providers,
  selected,
  onSelect,
}: {
  providers: string[];
  selected: string;
  onSelect: (p: string) => void;
}) {
  return (
    <div className="flex gap-2 flex-wrap mb-6">
      <button
        onClick={() => onSelect("all")}
        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
          selected === "all"
            ? "bg-white/10 text-white border border-white/20"
            : "bg-gray-800/50 text-gray-400 border border-transparent hover:border-white/10"
        }`}
      >
        All Providers
      </button>
      {providers.map((p) => {
        const meta = PROVIDER_META[p] ?? { icon: "🔧", color: "gray", label: p };
        return (
          <button
            key={p}
            onClick={() => onSelect(p)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
              selected === p
                ? COLOR_MAP[meta.color] + " border"
                : "bg-gray-800/50 text-gray-400 border border-transparent hover:border-white/10"
            }`}
          >
            <span>{meta.icon}</span>
            <span className="capitalize">{meta.label}</span>
          </button>
        );
      })}
    </div>
  );
}

function DeltaBadge({ improvement }: { improvement: number }) {
  const isPositive = improvement > 0;
  const isNeutral = improvement === 0;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono font-bold ${
        isPositive
          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
          : isNeutral
          ? "bg-gray-500/10 text-gray-400 border border-gray-500/20"
          : "bg-red-500/10 text-red-400 border border-red-500/20"
      }`}
    >
      <TrendingUp className={`w-3 h-3 ${!isPositive && !isNeutral ? "rotate-180" : ""}`} />
      {isPositive ? "+" : ""}{improvement.toFixed(2)}
    </span>
  );
}

function JobStatusBadge({ status }: { status: string }) {
  const config: Record<string, { icon: React.ReactNode; label: string; className: string }> = {
    completed: { icon: <CheckCircle2 className="w-3.5 h-3.5" />, label: "Done", className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    failed: { icon: <XCircle className="w-3.5 h-3.5" />, label: "Failed", className: "bg-red-500/10 text-red-400 border-red-500/20" },
    queued: { icon: <Clock className="w-3.5 h-3.5" />, label: "Queued", className: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
    running: { icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />, label: "Running", className: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
    optimizing: { icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />, label: "Evolving", className: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
    evaluating: { icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />, label: "Evaluating", className: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
  };
  const c = config[status] ?? { icon: <Clock className="w-3.5 h-3.5" />, label: status, className: "bg-gray-500/10 text-gray-400 border-gray-500/20" };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs border ${c.className}`}>
      {c.icon}
      {c.label}
    </span>
  );
}

function SkillCard({
  skill,
  provider,
  onEvolve,
  evolving,
  runs,
}: {
  skill: EvolvableSkill;
  provider: string;
  onEvolve: (skillName: string) => void;
  evolving: boolean;
  runs: EvolutionRun[];
}) {
  const meta = PROVIDER_META[provider] ?? { icon: "🔧", color: "gray", label: provider };
  const lastRun = runs
    .filter((r) => r.skill_name === skill.name)
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp))[0];

  return (
    <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-all group">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-white truncate">{skill.name}</h3>
          <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">
            {skill.description.replace(/^---\s*/, "").slice(0, 80) || "No description"}
          </p>
        </div>
        <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full border ${COLOR_MAP[meta.color]}`}>
          {meta.icon} {meta.label}
        </span>
      </div>

      <div className="flex items-center gap-3 mb-4">
        {skill.category && (
          <span className="text-[10px] uppercase tracking-wider text-gray-600 bg-gray-800/50 px-2 py-0.5 rounded">
            {skill.category}
          </span>
        )}
        {lastRun && <DeltaBadge improvement={lastRun.improvement} />}
      </div>

      <button
        onClick={() => onEvolve(skill.name)}
        disabled={evolving}
        className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
          evolving
            ? "bg-gray-800 text-gray-500 cursor-not-allowed"
            : lastRun
            ? "bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-400 border border-emerald-500/30 hover:from-emerald-500/30 hover:to-teal-500/30"
            : "bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 border border-blue-500/30 hover:from-blue-500/30 hover:to-purple-500/30"
        }`}
      >
        {evolving ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Evolving...
          </>
        ) : lastRun ? (
          <>
            <GitCompare className="w-4 h-4" />
            Re-Evolve
          </>
        ) : (
          <>
            <Zap className="w-4 h-4" />
            Evolve Now
          </>
        )}
      </button>
    </div>
  );
}

function StatsBar({ stats }: { stats: { totalSkills: number; totalProviders: number; totalRuns: number; avgImprovement: number } }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {[
        { label: "Skills", value: stats.totalSkills, icon: <Sparkles className="w-4 h-4" />, color: "emerald" },
        { label: "Providers", value: stats.totalProviders, icon: <Zap className="w-4 h-4" />, color: "violet" },
        { label: "Evolutions", value: stats.totalRuns, icon: <History className="w-4 h-4" />, color: "blue" },
        { label: "Avg Δ", value: `${stats.avgImprovement >= 0 ? "+" : ""}${stats.avgImprovement.toFixed(2)}`, icon: <TrendingUp className="w-4 h-4" />, color: stats.avgImprovement >= 0 ? "emerald" : "red" },
      ].map((stat) => (
        <div
          key={stat.label}
          className="bg-gray-900/50 border border-gray-800 rounded-xl p-4 flex items-center gap-3"
        >
          <div className={`p-2 rounded-lg bg-${stat.color}-500/10 text-${stat.color}-400`}>
            {stat.icon}
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stat.value}</div>
            <div className="text-xs text-gray-500">{stat.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Diff Viewer ────────────────────────────────────────────────────
function DiffViewer({ diff, onClose }: { diff: SkillDiff | null; onClose: () => void }) {
  if (!diff) return null;
  const improvement =
    diff.metrics && typeof diff.metrics === "object" && "improvement" in diff.metrics
      ? Number(diff.metrics.improvement)
      : 0;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-950 border border-gray-800 rounded-2xl w-full max-w-5xl max-h-[85vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-3">
              <GitCompare className="w-5 h-5 text-emerald-400" />
              {diff.skill_name}
            </h2>
            <p className="text-sm text-gray-500 mt-1">Before/After Comparison</p>
          </div>
          <div className="flex items-center gap-4">
            {diff.metrics && (
              <DeltaBadge improvement={improvement} />
            )}
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Metrics summary */}
        {diff.metrics && typeof diff.metrics === "object" && (
          <div className="px-6 py-4 border-b border-gray-800 bg-gray-900/30">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {Object.entries(diff.metrics).filter(([k]) => ["baseline_score", "evolved_score", "improvement", "elapsed_seconds", "iterations"].includes(k)).map(([key, val]) => (
                <div key={key} className="text-center">
                  <div className="text-xs text-gray-500 mb-1 capitalize">{key.replace(/_/g, " ")}</div>
                  <div className="text-lg font-mono font-bold text-white">
                    {key === "elapsed_seconds" ? `${Number(val).toFixed(1)}s` : key === "iterations" ? String(val) : Number(val).toFixed(3)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Side-by-side */}
        <div className="flex-1 overflow-auto grid grid-cols-2 divide-x divide-gray-800">
          {/* Baseline */}
          <div className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                BEFORE
              </span>
              <span className="text-xs text-gray-500">
                {diff.baseline ? `${diff.baseline.length} chars` : "N/A"}
              </span>
            </div>
            <pre className="text-xs text-gray-400 whitespace-pre-wrap font-mono leading-relaxed bg-gray-900/50 rounded-lg p-3 border border-gray-800 max-h-[50vh] overflow-auto">
              {diff.baseline?.slice(0, 5000) || "No baseline available"}
            </pre>
          </div>

          {/* Evolved */}
          <div className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                AFTER
              </span>
              <span className="text-xs text-gray-500">
                {diff.evolved ? `${diff.evolved.length} chars` : "N/A"}
              </span>
              {diff.metrics && (
                <DeltaBadge improvement={improvement} />
              )}
            </div>
            <pre className="text-xs text-gray-400 whitespace-pre-wrap font-mono leading-relaxed bg-gray-900/50 rounded-lg p-3 border border-gray-800 max-h-[50vh] overflow-auto">
              {diff.evolved?.slice(0, 5000) || "No evolved version available"}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────
export default function EvolutionHubPage() {
  const [providers, setProviders] = useState<EvolvableProvider[]>([]);
  const [providerNames, setProviderNames] = useState<string[]>([]);
  const [selectedProvider, setSelectedProvider] = useState("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [evolvingSkill, setEvolvingSkill] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [runs, setRuns] = useState<EvolutionRun[]>([]);
  const [selectedDiff, setSelectedDiff] = useState<SkillDiff | null>(null);
  const [error, setError] = useState("");

  // ── Data fetching ────────────────────────────────────────────────
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [evolvableData, runsData] = await Promise.all([
        api<EvolvableResponse>("/api/evolution/evolvable"),
        fetchEvolutionRuns().catch(() => [] as EvolutionRun[]),
      ]);

      if (evolvableData.status === "ok") {
        setProviders(evolvableData.providers);
        setProviderNames(evolvableData.providers.map((p) => p.provider));
      }
      setRuns(Array.isArray(runsData) ? runsData : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ── Poll active job ──────────────────────────────────────────────
  useEffect(() => {
    if (!activeJobId) return;
    const interval = setInterval(async () => {
      try {
        const job = await fetchJob(activeJobId);
        if (job.status === "completed" || job.status === "failed") {
          setEvolvingSkill(null);
          setActiveJobId(null);
          // Reload runs to show new data
          const runsData = await fetchEvolutionRuns().catch(() => [] as EvolutionRun[]);
          setRuns(Array.isArray(runsData) ? runsData : []);
        }
      } catch {
        // ignore poll errors
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [activeJobId]);

  // ── Actions ──────────────────────────────────────────────────────
  const handleEvolve = async (skillName: string) => {
    try {
      setEvolvingSkill(skillName);
      setError("");
      const result = await startEvolution(skillName, 3);
      if (result.error) {
        setError(result.error);
        setEvolvingSkill(null);
      } else {
        setActiveJobId(result.job_id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Evolution failed to start");
      setEvolvingSkill(null);
    }
  };

  const handleViewDiff = async (skillName: string, runDir?: string) => {
    try {
      // Find the run directory from runs
      const run = runs.find((r) => r.skill_name === skillName);
      if (!run) return;

      // Fetch diff
      const diffData = await fetchSkillDiff(skillName, "latest");
      setSelectedDiff(diffData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load diff");
    }
  };

  // ── Filtering ────────────────────────────────────────────────────
  const filteredSkills = providers
    .filter((p) => selectedProvider === "all" || p.provider === selectedProvider)
    .flatMap((p) =>
      p.skills
        .filter((s) => {
          const q = search.toLowerCase();
          return (
            !q ||
            s.name.toLowerCase().includes(q) ||
            s.description.toLowerCase().includes(q) ||
            s.category?.toLowerCase().includes(q)
          );
        })
        .map((s) => ({ ...s, _provider: p.provider }))
    );

  // ── Stats ────────────────────────────────────────────────────────
  const stats = {
    totalSkills: providers.reduce((acc, p) => acc + p.skills.length, 0),
    totalProviders: providers.length,
    totalRuns: runs.length,
    avgImprovement:
      runs.length > 0
        ? runs.reduce((acc, r) => acc + (r.improvement || 0), 0) / runs.length
        : 0,
  };

  // ── Render ───────────────────────────────────────────────────────
  return (
    <div className="min-h-screen px-6 py-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white flex items-center gap-3 mb-2">
          <Sparkles className="w-8 h-8 text-emerald-400" />
          Evolution Hub
        </h1>
        <p className="text-gray-500 text-lg">
          Multi-provider AI skill evolution — Hermes · Claude Code · OpenCode · Kilocode
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span className="text-sm">{error}</span>
          <button onClick={() => setError("")} className="ml-auto text-red-400 hover:text-red-300">
            ✕
          </button>
        </div>
      )}

      {/* Stats */}
      {!loading && <StatsBar stats={stats} />}

      {/* Filters */}
      {!loading && (
        <>
          <ProviderTabs
            providers={providerNames}
            selected={selectedProvider}
            onSelect={setSelectedProvider}
          />
          <div className="relative mb-6">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search skills..."
              className="w-full p-3 bg-gray-900 border border-gray-800 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500/50 transition-colors"
            />
          </div>
        </>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
        </div>
      )}

      {/* Skill Grid */}
      {!loading && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-12">
          {filteredSkills.map((skill) => (
            <SkillCard
              key={`${skill._provider}-${skill.name}`}
              skill={skill}
              provider={skill._provider}
              onEvolve={handleEvolve}
              evolving={evolvingSkill === skill.name}
              runs={runs}
            />
          ))}
          {filteredSkills.length === 0 && (
            <div className="col-span-full text-center py-16 text-gray-600">
              <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p className="text-lg">No skills found</p>
              <p className="text-sm mt-1">Try a different filter or search term</p>
            </div>
          )}
        </div>
      )}

      {/* Evolution History */}
      {!loading && runs.length > 0 && (
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2 mb-4">
            <History className="w-5 h-5 text-blue-400" />
            Evolution History
          </h2>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800 text-left">
                    <th className="p-4 text-gray-500 font-medium">Skill</th>
                    <th className="p-4 text-gray-500 font-medium">Date</th>
                    <th className="p-4 text-gray-500 font-medium">Baseline</th>
                    <th className="p-4 text-gray-500 font-medium">Evolved</th>
                    <th className="p-4 text-gray-500 font-medium">Δ Delta</th>
                    <th className="p-4 text-gray-500 font-medium">Time</th>
                    <th className="p-4 text-gray-500 font-medium">Status</th>
                    <th className="p-4 text-gray-500 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.slice(0, 50).map((run, i) => (
                    <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                      <td className="p-4 font-medium text-white">{run.skill_name}</td>
                      <td className="p-4 text-gray-400 font-mono text-xs">
                        {run.timestamp.slice(0, 10)}
                      </td>
                      <td className="p-4 font-mono text-gray-400">
                        {(run.baseline_score ?? 0).toFixed(3)}
                      </td>
                      <td className="p-4 font-mono text-gray-400">
                        {(run.evolved_score ?? 0).toFixed(3)}
                      </td>
                      <td className="p-4">
                        <DeltaBadge improvement={run.improvement ?? 0} />
                      </td>
                      <td className="p-4 text-gray-500 font-mono text-xs">
                        {(run.elapsed_seconds ?? 0).toFixed(1)}s
                      </td>
                      <td className="p-4">
                        {run.constraints_passed !== undefined ? (
                          run.constraints_passed ? (
                            <span className="text-emerald-400 text-xs font-medium">✓ Pass</span>
                          ) : (
                            <span className="text-amber-400 text-xs font-medium">⚠ Issues</span>
                          )
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>
                      <td className="p-4">
                        <button
                          onClick={() => handleViewDiff(run.skill_name)}
                          className="text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
                        >
                          <GitCompare className="w-3 h-3" />
                          Compare
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Diff Viewer Modal */}
      <DiffViewer diff={selectedDiff} onClose={() => setSelectedDiff(null)} />
    </div>
  );
}
