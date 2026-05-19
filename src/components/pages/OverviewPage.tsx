"use client"

import { useState, useEffect, useMemo, useCallback } from "react"
import { motion } from "framer-motion"
import { prepare } from "@chenglou/pretext"
import {
  Activity,
  GitBranch,
  TrendingUp,
  CheckCircle2,
  XCircle,
  Cpu,
  Dna,
  Layers,
  Clock,
  Zap,
  ArrowUpRight,
} from "lucide-react"
import { fetchHealth, fetchMetrics, type MetricsData, type EvolutionRun } from "@/lib/api"
import { CountUp, SpotlightCard } from "@/components/bits"
import { cn } from "@/lib/utils"

// ═══════════════════════════════════════════════════════════════════
// Icon Registry
// ═══════════════════════════════════════════════════════════════════

const iconMap: Record<string, React.ElementType> = {
  "git-branch": GitBranch,
  cpu: Cpu,
  "trending-up": TrendingUp,
  activity: Activity,
  clock: Clock,
  zap: Zap,
  layers: Layers,
  dna: Dna,
}

function resolveIcon(key: string): React.ElementType {
  return iconMap[key] ?? Activity
}

// ═══════════════════════════════════════════════════════════════════
// Components
// ═══════════════════════════════════════════════════════════════════

// ── Genoma Stat Card ──────────────────────────────────────────────────
function StatCard({
  label,
  value,
  suffix = "",
  icon,
  color,
  delay,
  trend,
}: {
  label: string
  value: number
  suffix?: string
  icon: string
  color: string
  delay: number
  trend?: number
}) {
  const IconComponent = resolveIcon(icon)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4, ease: "easeOut" }}
    >
      <SpotlightCard
        spotlightColor={`${color}10`}
        className={cn(
          // Genoma glass card — no border
          "relative overflow-hidden rounded-2xl p-5",
          "bg-white/70 dark:bg-[#0f1a2e]/80",
          "backdrop-blur-xl",
          "editorial-shadow",
          "group hover:shadow-lg transition-shadow duration-300",
        )}
      >
        {/* Top row: label + icon */}
        <div className="flex items-center justify-between mb-3">
          <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-[0.12em]">
            {label}
          </span>
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: `${color}12` }}
          >
            <IconComponent className="w-4 h-4" style={{ color }} />
          </div>
        </div>

        {/* Value — CountUp animation */}
        <div className="flex items-baseline gap-1.5">
          <p className="text-[1.75rem] font-bold font-heading tracking-tight stat-number"
            style={{ color: "var(--genoma-primary, #002444)" }}>
            <CountUp to={value} duration={1.2} delay={delay} />
            {suffix}
          </p>

          {/* Trend pill */}
          {trend !== undefined && trend !== 0 && (
            <span className={cn(
              "inline-flex items-center gap-0.5 text-[11px] font-medium px-1.5 py-0.5 rounded-full",
              trend > 0
                ? "text-[#16a34a] bg-[#16a34a]/8"
                : "text-[#dc2626] bg-[#dc2626]/8"
            )}>
              <ArrowUpRight className={cn("w-3 h-3", trend < 0 && "rotate-180")} />
              {Math.abs(trend)}%
            </span>
          )}
        </div>
      </SpotlightCard>
    </motion.div>
  )
}

// ── Run Row — Genoma style ────────────────────────────────────────────
function RunRow({
  run,
  index,
  isExpanded,
  onToggle,
}: {
  run: EvolutionRun
  index: number
  isExpanded: boolean
  onToggle: () => void
}) {
  const improved = run.improvement > 0
  const improvementPct = Math.round(run.improvement * 100)

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.5 + index * 0.05, duration: 0.3 }}
    >
      <button
        onClick={onToggle}
        className={cn(
          "w-full text-left",
          // Genoma card row — no dividers, spacing-based separation
          "flex items-center gap-3 py-3.5 px-4 rounded-xl",
          "bg-white/50 dark:bg-[#0f1a2e]/50",
          "hover:bg-white/80 dark:hover:bg-[#0f1a2e]/80",
          "transition-all duration-200",
          "group",
          isExpanded && "bg-[#fcf9f8] dark:bg-[#0a1525] shadow-sm",
        )}
      >
        {/* Status dot */}
        <div className="flex-shrink-0">
          {run.constraints_passed ? (
            <CheckCircle2 className="w-4 h-4 text-[#16a34a]" />
          ) : (
            <XCircle className="w-4 h-4 text-[#dc2626]" />
          )}
        </div>

        {/* Skill name + timestamp */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-foreground truncate">
            {run.skill_name}
          </p>
          <p className="text-[11px] text-muted-foreground font-mono">
            {run.timestamp}
          </p>
        </div>

        {/* Score delta — the money shot */}
        <div className="text-right flex-shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-muted-foreground font-mono">
              {(run.baseline_score * 100).toFixed(0)}%
            </span>
            <span className="text-[10px] text-muted-foreground">→</span>
            <span className={cn(
              "text-sm font-semibold font-mono",
              improved ? "text-[#16a34a]" : "text-[#dc2626]"
            )}>
              {(run.evolved_score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center justify-end gap-2 mt-0.5">
            {improved ? (
              <span className="inline-flex items-center gap-0.5 text-[10px] font-medium text-[#16a34a]">
                <TrendingUp className="w-3 h-3" />+{improvementPct}%
              </span>
            ) : (
              <span className="text-[10px] text-muted-foreground">
                {improvementPct}%
              </span>
            )}
            <span className="text-[10px] text-muted-foreground/60 font-mono">
              {run.iterations}it · {run.elapsed_seconds.toFixed(0)}s
            </span>
          </div>
        </div>
      </button>

      {/* Expanded: inline detail (Pretext would handle this in prod) */}
      {isExpanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="overflow-hidden"
        >
          <div className="px-4 pb-3 pt-1">
            <div className={cn(
              "rounded-lg p-3 text-xs font-mono",
              "bg-[#f6f3f2] dark:bg-[#0a1525]",
              "border-l-[3px]",
              run.constraints_passed
                ? "border-l-[#16a34a]"
                : "border-l-[#dc2626]"
            )}>
              <div className="flex gap-4 text-muted-foreground">
                <span>Baseline: {(run.baseline_score * 100).toFixed(1)}%</span>
                <span>Evolved: {(run.evolved_score * 100).toFixed(1)}%</span>
                <span>Δ: {(run.improvement * 100).toFixed(1)}%</span>
                <span>{run.iterations} iterations</span>
                <span>{run.elapsed_seconds.toFixed(1)}s</span>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

// ═══════════════════════════════════════════════════════════════════
// OverviewPage
// ═══════════════════════════════════════════════════════════════════

export default function OverviewPage() {
  const [health, setHealth] = useState<{
    status: string
    skills_count: number
    categories: Record<string, number>
  } | null>(null)
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedRun, setExpandedRun] = useState<number | null>(null)

  useEffect(() => {
    Promise.all([fetchHealth(), fetchMetrics()])
      .then(([h, m]) => {
        setHealth(h)
        setMetrics(m)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Derive stats for the card grid
  const stats = useMemo(() => [
    {
      label: "Evolution Runs",
      value: metrics?.total_runs ?? 0,
      icon: "git-branch",
      color: "#002444",
      delay: 0.1,
    },
    {
      label: "Skills Evolved",
      value: metrics?.skills_evolved ?? 0,
      icon: "cpu",
      color: "#0891b2",
      delay: 0.2,
    },
    {
      label: "Avg Improvement",
      value: Math.round((metrics?.avg_improvement ?? 0) * 100),
      suffix: "%",
      icon: "trending-up",
      color: "#16a34a",
      delay: 0.3,
    },
    {
      label: "Success Rate",
      value: Math.round((metrics?.success_rate ?? 0) * 100),
      suffix: "%",
      icon: "activity",
      color: "#a93800",
      delay: 0.4,
    },
  ], [metrics])

  return (
    <div className="space-y-6 max-w-6xl">
      {/* ═══ Hero — Genoma Editorial ═══ */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative overflow-hidden rounded-2xl p-8 md:p-10
          bg-[#002444] dark:bg-[#001830]
          editorial-shadow"
      >
        {/* Ambient gradient blobs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div
            className="absolute -top-24 -right-24 w-80 h-80 rounded-full opacity-[0.07]"
            style={{
              background: "radial-gradient(circle, #a93800 0%, transparent 70%)",
            }}
          />
          <div
            className="absolute -bottom-16 -left-16 w-64 h-64 rounded-full opacity-[0.05]"
            style={{
              background: "radial-gradient(circle, #ffb94c 0%, transparent 70%)",
            }}
          />
        </div>

        <div className="relative">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 mb-3 px-3 py-1 rounded-full
            bg-[#a93800]/15 border border-[#a93800]/20">
            <Dna className="w-3.5 h-3.5 text-[#fc713a]" />
            <span className="text-[11px] font-medium text-[#fc713a] uppercase tracking-[0.1em]">
              Autonomous Evolution Interface
            </span>
          </div>

          <h1 className="text-3xl md:text-4xl font-bold font-heading text-[#fcf9f8] tracking-tight">
            <span className="gradient-text">Genoma</span>
          </h1>
          <p className="text-[#fcf9f8]/60 mt-2 text-sm md:text-base max-w-lg">
            Self-evolving intelligence. Full observability. Zero-friction evolution.
          </p>

          {/* Status row */}
          <div className="flex items-center gap-2 mt-5">
            <div
              className={cn(
                "w-2 h-2 rounded-full",
                loading
                  ? "bg-[#ffb94c] animate-pulse"
                  : health
                  ? "bg-[#22c55e] led-pulse"
                  : "bg-[#dc2626]"
              )}
              style={{ color: health ? "#22c55e" : loading ? "#ffb94c" : "#dc2626" }}
            />
            <span className="text-xs text-[#fcf9f8]/50">
              {loading
                ? "Conectando..."
                : health
                ? `Backend online · ${health.skills_count} skills`
                : "Backend offline"}
            </span>
          </div>
        </div>
      </motion.div>

      {/* ═══ Stats Grid ═══ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>

      {/* ═══ Recent Evolution Runs ═══ */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.4 }}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#a93800]" />
            <h2 className="text-sm font-semibold uppercase tracking-[0.1em] text-foreground/70">
              Recent Evolution Runs
            </h2>
          </div>
          {metrics?.runs?.length ? (
            <span className="text-[11px] text-muted-foreground font-mono">
              {metrics.runs.length} runs
            </span>
          ) : null}
        </div>

        {metrics?.runs?.length ? (
          <div className="space-y-1.5">
            {metrics.runs.slice(0, 8).map((run, i) => (
              <RunRow
                key={`${run.skill_name}-${run.timestamp}`}
                run={run}
                index={i}
                isExpanded={expandedRun === i}
                onToggle={() =>
                  setExpandedRun(expandedRun === i ? null : i)
                }
              />
            ))}
          </div>
        ) : (
          <div className={cn(
            "rounded-2xl p-12 text-center",
            "bg-white/40 dark:bg-[#0f1a2e]/50",
            "editorial-shadow",
          )}>
            <Dna className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">
              No evolution runs yet. Start one from the Evolution tab.
            </p>
          </div>
        )}
      </motion.div>
    </div>
  )
}
