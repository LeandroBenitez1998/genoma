"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  TrendingUp,
  Clock,
  Target,
  Loader2,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { fetchMetrics, type MetricsData, type EvolutionRun } from "@/lib/api";

function BarChart({
  data,
  label,
  color,
}: {
  data: { label: string; value: number }[];
  label: string;
  color: string;
}) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div>
      <p className="text-xs text-muted-foreground mb-3 uppercase tracking-wider">
        {label}
      </p>
      <div className="space-y-2">
        {data.map((d, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="text-[10px] font-mono text-muted-foreground w-20 truncate">
              {d.label}
            </span>
            <div className="flex-1 h-4 bg-white/[0.03] rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(d.value / max) * 100}%` }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="h-full rounded-full"
                style={{ backgroundColor: color }}
              />
            </div>
            <span className="text-[10px] font-mono text-muted-foreground w-12 text-right">
              {(d.value * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics()
      .then(setMetrics)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Aggregate scores by skill
  const skillScores: Record<string, { total: number; count: number }> = {};
  metrics?.runs.forEach((run) => {
    if (!skillScores[run.skill_name])
      skillScores[run.skill_name] = { total: 0, count: 0 };
    skillScores[run.skill_name].total += run.evolved_score;
    skillScores[run.skill_name].count += 1;
  });

  const skillChartData = Object.entries(skillScores).map(([name, s]) => ({
    label: name,
    value: s.total / s.count,
  }));

  // Improvement per run
  const improvementData =
    metrics?.runs.map((run) => ({
      label: `${run.skill_name} ${run.timestamp?.slice(0, 8) || ""}`,
      value: run.improvement ?? 0,
    })) ?? [];

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: "Total Runs",
            value: String(metrics?.total_runs ?? 0),
            icon: <BarChart3 className="w-4 h-4" />,
            color: "#8b5cf6",
          },
          {
            label: "Success Rate",
            value: `${((metrics?.success_rate ?? 0) * 100).toFixed(0)}%`,
            icon: <Target className="w-4 h-4" />,
            color: "#22c55e",
          },
          {
            label: "Best Improvement",
            value: `${((metrics?.best_improvement ?? 0) * 100).toFixed(1)}%`,
            icon: <TrendingUp className="w-4 h-4" />,
            color: "#06b6d4",
          },
          {
            label: "Avg Time",
            value: `${(metrics?.avg_time_seconds ?? 0).toFixed(0)}s`,
            icon: <Clock className="w-4 h-4" />,
            color: "#eab308",
          },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card rounded-2xl p-5"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground uppercase tracking-wider">
                {stat.label}
              </span>
              <span style={{ color: stat.color }}>{stat.icon}</span>
            </div>
            <p className="text-2xl font-bold font-mono">{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card rounded-2xl p-6"
        >
          <h3 className="text-sm font-semibold uppercase tracking-wider mb-4">
            Score by Skill
          </h3>
          {skillChartData.length ? (
            <BarChart data={skillChartData} label="" color="#8b5cf6" />
          ) : (
            <p className="text-sm text-muted-foreground py-8 text-center">
              No data yet.
            </p>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-card rounded-2xl p-6"
        >
          <h3 className="text-sm font-semibold uppercase tracking-wider mb-4">
            Improvement per Run
          </h3>
          {improvementData.length ? (
            <BarChart data={improvementData} label="" color="#06b6d4" />
          ) : (
            <p className="text-sm text-muted-foreground py-8 text-center">
              No data yet.
            </p>
          )}
        </motion.div>
      </div>

      {/* Full run table */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="glass-card rounded-2xl p-6"
      >
        <h3 className="text-sm font-semibold uppercase tracking-wider mb-4">
          All Runs
        </h3>
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          </div>
        ) : metrics?.runs?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-muted-foreground border-b border-white/[0.06]">
                  <th className="text-left py-2 px-3">Status</th>
                  <th className="text-left py-2 px-3">Skill</th>
                  <th className="text-left py-2 px-3">Timestamp</th>
                  <th className="text-right py-2 px-3">Baseline</th>
                  <th className="text-right py-2 px-3">Evolved</th>
                  <th className="text-right py-2 px-3">Δ</th>
                  <th className="text-right py-2 px-3">Time</th>
                </tr>
              </thead>
              <tbody>
                {metrics.runs.map((run, i) => (
                  <tr
                    key={i}
                    className="border-b border-white/[0.03] hover:bg-white/[0.02]"
                  >
                    <td className="py-2 px-3">
                      {run.constraints_passed ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-success" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-error" />
                      )}
                    </td>
                    <td className="py-2 px-3 font-medium">{run.skill_name}</td>
                    <td className="py-2 px-3 font-mono text-muted-foreground">
                      {run.timestamp}
                    </td>
                    <td className="py-2 px-3 text-right font-mono">
                      {(run.baseline_score * 100).toFixed(0)}%
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-accent-violet">
                      {(run.evolved_score * 100).toFixed(0)}%
                    </td>
                    <td className="py-2 px-3 text-right font-mono">
                      {(run.improvement ?? 0) > 0 ? "+" : ""}
                      {((run.improvement ?? 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-muted-foreground">
                      {run.elapsed_seconds?.toFixed(0)}s
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground py-8 text-center">
            No runs recorded.
          </p>
        )}
      </motion.div>
    </div>
  );
}
