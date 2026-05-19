"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Dna,
  Activity,
  Clock,
  Pin,
  PinOff,
  Archive,
  ArchiveRestore,
  Play,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Trash2,
  RefreshCw,
  FileText,
  Eye,
  MousePointerClick,
  Code2,
  TrendingUp,
  WifiOff,
  Search,
} from "lucide-react";
import {
  fetchCuratorStatus,
  fetchCuratorSkills,
  fetchCuratorReports,
  fetchCuratorReport,
  curatorPin,
  curatorUnpin,
  curatorRestore,
  curatorRun,
  fetchCuratorReport as fetchCuratorReportDetail,
  type CuratorStatus,
  type CuratorSkillUsage,
  type CuratorReport,
  type CuratorReportDetail,
} from "@/lib/api";
import { SpotlightCard, CountUp } from "@/components/bits";

// ── Helpers ────────────────────────────────────────────────────────

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("es-MX", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function stateColor(state: string): string {
  switch (state) {
    case "active": return "#22c55e";
    case "stale": return "#eab308";
    case "archived": return "#ef4444";
    case "untracked": return "#6b7280";
    default: return "#6b7280";
  }
}

function stateLabel(state: string): string {
  switch (state) {
    case "active": return "Active";
    case "stale": return "Stale";
    case "archived": return "Archived";
    case "untracked": return "Untracked";
    default: return state;
  }
}

function StateBadge({ state }: { state: string }) {
  const colors: Record<string, string> = {
    active: "bg-[#22c55e]/10 text-[#22c55e] border-[#22c55e]/20",
    stale: "bg-[#eab308]/10 text-[#eab308] border-[#eab308]/20",
    archived: "bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/20",
    untracked: "bg-[#6b7280]/10 text-[#6b7280] border-[#6b7280]/20",
  };
  return (
    <span
      className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${
        colors[state] || colors.untracked
      }`}
    >
      {stateLabel(state)}
    </span>
  );
}

// ── Sub-components ─────────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon,
  color,
  delay,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
    >
      <SpotlightCard
        spotlightColor={`${color}15`}
        className="glass-card rounded-2xl p-5"
      >
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">
            {label}
          </span>
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${color}15` }}
          >
            <span style={{ color }}>{icon}</span>
          </div>
        </div>
        <p className="text-2xl font-bold font-mono tracking-tight">
          <CountUp to={value} duration={1.5} delay={delay} />
        </p>
      </SpotlightCard>
    </motion.div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────

export default function CuratorPage() {
  const [status, setStatus] = useState<CuratorStatus | null>(null);
  const [skills, setSkills] = useState<CuratorSkillUsage[]>([]);
  const [reports, setReports] = useState<CuratorReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState<string>("all");
  const [selectedReport, setSelectedReport] = useState<CuratorReportDetail | null>(null);
  const [runResult, setRunResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, sk, r] = await Promise.all([
        fetchCuratorStatus(),
        fetchCuratorSkills(),
        fetchCuratorReports(),
      ]);
      setStatus(s);
      setSkills(sk.skills);
      setReports(r.reports);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch curator data");
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleRun = async () => {
    setRunning(true);
    setRunResult(null);
    try {
      const result = await curatorRun(false);
      setRunResult(result.status === "ok" ? `✅ Curator run complete (report: ${result.report_id})` : `❌ ${result.status}`);
      await fetchAll();
    } catch (err) {
      setRunResult(`❌ ${err instanceof Error ? err.message : "Run failed"}`);
    }
    setRunning(false);
  };

  const handlePin = async (skill: string, currentlyPinned: boolean) => {
    try {
      if (currentlyPinned) {
        await curatorUnpin(skill);
      } else {
        await curatorPin(skill);
      }
      await Promise.all([fetchCuratorStatus(), fetchCuratorSkills().then(r => setSkills(r.skills))]);
    } catch (err) {
      console.error("Pin/unpin failed:", err);
    }
  };

  const handleRestore = async (skill: string) => {
    try {
      await curatorRestore(skill);
      await fetchAll();
    } catch (err) {
      console.error("Restore failed:", err);
    }
  };

  const handleViewReport = async (reportId: string) => {
    try {
      const detail = await fetchCuratorReportDetail(reportId);
      setSelectedReport(detail);
    } catch (err) {
      console.error("Failed to load report:", err);
    }
  };

  // Filter skills
  const filteredSkills = skills.filter((s) => {
    if (stateFilter !== "all" && s.state !== stateFilter) return false;
    if (search && !s.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="min-h-[20rem] flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-accent-cyan animate-spin mr-2" />
        <span className="text-muted-foreground">Loading Curator...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[20rem] flex flex-col items-center justify-center gap-4">
        <WifiOff className="w-12 h-12 text-error" />
        <p className="text-muted-foreground">{error}</p>
        <button
          onClick={fetchAll}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent-violet/10 text-accent-violet hover:bg-accent-violet/20 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl p-8 glass-card"
      >
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div
            className="absolute -top-20 -right-20 w-64 h-64 rounded-full opacity-10"
            style={{
              background:
                "radial-gradient(circle, rgba(34,197,94,0.5) 0%, transparent 70%)",
            }}
          />
        </div>
        <div className="relative">
          <div className="flex items-center gap-2 mb-2">
            <Dna className="w-5 h-5 text-success" />
            <span className="text-xs font-medium text-success uppercase tracking-wider">
              Skill Lifecycle Management
            </span>
          </div>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold">
                <span className="gradient-text">Curator</span>
              </h1>
              <p className="text-muted-foreground mt-2 text-sm">
                Background maintenance for agent-created skills. Active → Stale → Archived lifecycle.
              </p>
            </div>
            <div className="flex items-center gap-3">
              {runResult && (
                <span className="text-xs text-muted-foreground max-w-[200px] truncate">
                  {runResult}
                </span>
              )}
              <button
                onClick={handleRun}
                disabled={running}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent-violet/10 text-accent-violet hover:bg-accent-violet/20 border border-accent-violet/20 disabled:opacity-50 transition-colors text-sm"
              >
                {running ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {running ? "Running..." : "Run Curator"}
              </button>
              <button
                onClick={fetchAll}
                className="p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/[0.06] transition-colors"
                title="Refresh"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Stats grid */}
      {status && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
          <StatCard label="Active" value={status.stats.active} icon={<Activity className="w-4 h-4" />} color="#22c55e" delay={0.05} />
          <StatCard label="Stale" value={status.stats.stale} icon={<AlertTriangle className="w-4 h-4" />} color="#eab308" delay={0.1} />
          <StatCard label="Archived" value={status.stats.archived} icon={<Archive className="w-4 h-4" />} color="#ef4444" delay={0.15} />
          <StatCard label="Pinned" value={status.stats.pinned} icon={<Pin className="w-4 h-4" />} color="#8b5cf6" delay={0.2} />
          <StatCard label="Total Tracked" value={status.stats.total} icon={<Dna className="w-4 h-4" />} color="#06b6d4" delay={0.25} />
          <StatCard label="Reports" value={reports.length} icon={<FileText className="w-4 h-4" />} color="#f97316" delay={0.3} />
        </div>
      )}

      {/* Last run info + LRU */}
      {status && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-4"
        >
          <SpotlightCard spotlightColor="rgba(6,182,212,0.08)" className="glass-card rounded-2xl p-5">
            <h3 className="text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-2 mb-3">
              <Clock className="w-3 h-3" />
              Last Curator Run
            </h3>
            {status.last_run?.timestamp ? (
              <div>
                <p className="text-sm font-mono">{formatDate(status.last_run.timestamp as string)}</p>
                {status.last_run_dir && (
                  <p className="text-[10px] text-muted-foreground mt-1">
                    Report: {status.last_run_dir}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No runs yet</p>
            )}
          </SpotlightCard>

          <SpotlightCard spotlightColor="rgba(234,179,8,0.08)" className="glass-card rounded-2xl p-5">
            <h3 className="text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-2 mb-3">
              <TrendingUp className="w-3 h-3" />
              Least Recently Used (Top 5)
            </h3>
            {status.least_recently_used?.length > 0 ? (
              <div className="space-y-1.5">
                {status.least_recently_used.map((s, i) => (
                  <div key={s.name} className="flex items-center justify-between text-xs">
                    <span className="font-mono truncate max-w-[180px]">{s.name}</span>
                    <span className="text-muted-foreground">{formatDate(s.last_used)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No usage data yet</p>
            )}
          </SpotlightCard>
        </motion.div>
      )}

      {/* Skill health table */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-card rounded-2xl p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-accent-cyan" />
            Skill Health
          </h2>
          <div className="flex items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search skills..."
                className="w-40 pl-8 pr-3 py-1.5 text-xs rounded-lg bg-white/[0.03] border border-white/[0.08] text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-accent-violet/40"
              />
            </div>
            {/* State filter */}
            <select
              value={stateFilter}
              onChange={(e) => setStateFilter(e.target.value)}
              className="text-xs px-2 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.08] text-foreground focus:outline-none focus:border-accent-violet/40"
            >
              <option value="all">All States</option>
              <option value="active">Active</option>
              <option value="stale">Stale</option>
              <option value="archived">Archived</option>
              <option value="untracked">Untracked</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-white/[0.06] text-muted-foreground uppercase tracking-wider">
                <th className="text-left py-2 pr-3 font-medium">Skill</th>
                <th className="text-left py-2 px-3 font-medium">State</th>
                <th className="text-center py-2 px-3 font-medium">Uses</th>
                <th className="text-center py-2 px-3 font-medium">Views</th>
                <th className="text-center py-2 px-3 font-medium">Patches</th>
                <th className="text-left py-2 px-3 font-medium">Last Used</th>
                <th className="text-center py-2 px-3 font-medium">Created</th>
                <th className="text-center py-2 px-3 font-medium">Agent</th>
                <th className="text-right py-2 pl-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredSkills.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-muted-foreground">
                    {search || stateFilter !== "all"
                      ? "No skills match your filters"
                      : "No skills tracked yet. Run the curator to start tracking."}
                  </td>
                </tr>
              )}
              {filteredSkills.map((skill, i) => (
                <motion.tr
                  key={skill.name}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.02 * i }}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                >
                  <td className="py-2.5 pr-3">
                    <span className="font-mono text-xs font-medium">{skill.name}</span>
                  </td>
                  <td className="py-2.5 px-3">
                    <StateBadge state={skill.state} />
                  </td>
                  <td className="py-2.5 px-3 text-center font-mono">{skill.use_count}</td>
                  <td className="py-2.5 px-3 text-center font-mono">{skill.view_count}</td>
                  <td className="py-2.5 px-3 text-center font-mono">{skill.patch_count}</td>
                  <td className="py-2.5 px-3 text-muted-foreground font-mono">{formatDate(skill.last_used_at)}</td>
                  <td className="py-2.5 px-3 text-muted-foreground font-mono">{formatDate(skill.created_at)}</td>
                  <td className="py-2.5 px-3 text-center">
                    <span
                      className={`inline-block w-2 h-2 rounded-full ${
                        skill.agent_created ? "bg-accent-cyan" : "bg-muted"
                      }`}
                      title={skill.agent_created ? "Agent-created" : "Bundled/Hub"}
                    />
                  </td>
                  <td className="py-2.5 pl-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {skill.state === "archived" ? (
                        <button
                          onClick={() => handleRestore(skill.name)}
                          className="p-1.5 rounded-lg text-muted-foreground hover:text-success hover:bg-success/10 transition-colors"
                          title="Restore from archive"
                        >
                          <ArchiveRestore className="w-3.5 h-3.5" />
                        </button>
                      ) : skill.agent_created ? (
                        <button
                          onClick={() => handlePin(skill.name, skill.pinned)}
                          className={`p-1.5 rounded-lg transition-colors ${
                            skill.pinned
                              ? "text-accent-violet hover:bg-accent-violet/10"
                              : "text-muted-foreground hover:text-foreground hover:bg-white/[0.06]"
                          }`}
                          title={skill.pinned ? "Unpin skill" : "Pin skill"}
                        >
                          {skill.pinned ? (
                            <PinOff className="w-3.5 h-3.5" />
                          ) : (
                            <Pin className="w-3.5 h-3.5" />
                          )}
                        </button>
                      ) : null}
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Reports timeline */}
      {reports.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-card rounded-2xl p-6"
        >
          <h2 className="text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            <FileText className="w-4 h-4 text-accent-cyan" />
            Curator Reports
          </h2>

          <div className="space-y-2">
            {reports.map((report, i) => (
              <div
                key={report.id}
                className="flex items-center justify-between py-2.5 px-4 rounded-xl border border-white/[0.04] hover:bg-white/[0.02] transition-colors cursor-pointer"
                onClick={() => handleViewReport(report.id)}
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div>
                    <p className="text-sm font-mono">{report.id}</p>
                    {report.summary && (
                      <p className="text-[10px] text-muted-foreground">
                        {report.summary.skills_reviewed} skills reviewed
                        {report.summary.archived > 0 && ` · ${report.summary.archived} archived`}
                        {report.summary.patched > 0 && ` · ${report.summary.patched} patched`}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {report.has_report && (
                    <span className="text-[10px] text-accent-cyan bg-accent-cyan/10 px-2 py-0.5 rounded-full">
                      REPORT.md
                    </span>
                  )}
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Report detail modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setSelectedReport(null)}>
          <div className="max-w-3xl w-full max-h-[80vh] overflow-y-auto m-4 rounded-2xl glass-card p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold font-mono">{selectedReport.id}</h3>
              <button
                onClick={() => setSelectedReport(null)}
                className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/[0.06]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {selectedReport.run_data && (
              <div className="mb-4">
                <h4 className="text-xs uppercase tracking-wider text-muted-foreground mb-2">Run Data</h4>
                <pre className="text-xs font-mono bg-white/[0.03] rounded-xl p-4 overflow-x-auto">
                  {JSON.stringify(selectedReport.run_data, null, 2)}
                </pre>
              </div>
            )}

            {selectedReport.report_md && (
              <div>
                <h4 className="text-xs uppercase tracking-wider text-muted-foreground mb-2">Report</h4>
                <div className="text-xs font-mono bg-white/[0.03] rounded-xl p-4 whitespace-pre-wrap">
                  {selectedReport.report_md}
                </div>
              </div>
            )}

            {!selectedReport.run_data && !selectedReport.report_md && (
              <p className="text-sm text-muted-foreground">No report data available.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Needed for the report detail modal
function ChevronRight({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

function X({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
