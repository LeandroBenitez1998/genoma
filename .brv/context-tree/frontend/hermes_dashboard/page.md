---
title: Page
summary: Source file app/skills/page.tsx in the Next.js frontend
tags: []
related: [frontend/hermes_dashboard/hermes_dashboard_frontend.md, frontend/hermes_dashboard/architecture_overview.md, frontend/hermes_dashboard/layout.md, frontend/hermes_dashboard/globals.md, frontend/hermes_dashboard/route.md]
keywords: []
createdAt: '2026-05-21T07:39:26.008Z'
updatedAt: '2026-05-21T07:39:26.017Z'
---
## Reason
Curate app/skills/page.tsx from src folder

## Raw Concept
**Task:**
Document app/skills/page.tsx

**Timestamp:** 2026-05-21

## Narrative
### Structure
Implementation for app/skills/page.tsx

### Highlights
Captured complete source content from app/skills/page.tsx

---

&quot;use client&quot;;

import { useState, useEffect, useCallback } from &quot;react&quot;;
import { api, startEvolution, fetchJobs, fetchJob, fetchSkillDiff, fetchEvolutionRuns } from &quot;@/lib/api&quot;;
import type { EvolutionJob, EvolutionRun, SkillDiff } from &quot;@/lib/api&quot;;
import {
  Zap, TrendingUp, GitCompare, History, Loader2, Play,
  CheckCircle2, XCircle, Clock, Sparkles, AlertTriangle,
} from &quot;lucide-react&quot;;

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
const PROVIDER_META: Record&lt;string, { icon: string; color: string; label: string }&gt; = {
  hermes: { icon: &quot;🪽&quot;, color: &quot;emerald&quot;, label: &quot;Hermes&quot; },
  &quot;claude-code&quot;: { icon: &quot;🤖&quot;, color: &quot;violet&quot;, label: &quot;Claude Code&quot; },
  opencode: { icon: &quot;💻&quot;, color: &quot;blue&quot;, label: &quot;OpenCode&quot; },
  kilocode: { icon: &quot;⚡&quot;, color: &quot;amber&quot;, label: &quot;Kilocode&quot; },
  antigravity: { icon: &quot;🚀&quot;, color: &quot;rose&quot;, label: &quot;Antigravity&quot; },
};

const COLOR_MAP: Record&lt;string, string&gt; = {
  emerald: &quot;bg-emerald-500/10 border-emerald-500/30 text-emerald-400&quot;,
  violet: &quot;bg-violet-500/10 border-violet-500/30 text-violet-400&quot;,
  blue: &quot;bg-blue-500/10 border-blue-500/30 text-blue-400&quot;,
  amber: &quot;bg-amber-500/10 border-amber-500/30 text-amber-400&quot;,
  rose: &quot;bg-rose-500/10 border-rose-500/30 text-rose-400&quot;,
};

// ── Sub-components ─────────────────────────────────────────────────

function ProviderTabs({
  providers,
  selected,
  onSelect,
}: {
  providers: string[];
  selected: string;
  onSelect: (p: string) =&gt; void;
}) {
  return (
    &lt;div className=&quot;flex gap-2 flex-wrap mb-6&quot;&gt;
      &lt;button
        onClick={() =&gt; onSelect(&quot;all&quot;)}
        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
          selected === &quot;all&quot;
            ? &quot;bg-white/10 text-white border border-white/20&quot;
            : &quot;bg-gray-800/50 text-gray-400 border border-transparent hover:border-white/10&quot;
        }`}
      &gt;
        All Providers
      &lt;/button&gt;
      {providers.map((p) =&gt; {
        const meta = PROVIDER_META[p] ?? { icon: &quot;🔧&quot;, color: &quot;gray&quot;, label: p };
        return (
          &lt;button
            key={p}
            onClick={() =&gt; onSelect(p)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
              selected === p
                ? COLOR_MAP[meta.color] + &quot; border&quot;
                : &quot;bg-gray-800/50 text-gray-400 border border-transparent hover:border-white/10&quot;
            }`}
          &gt;
            &lt;span&gt;{meta.icon}&lt;/span&gt;
            &lt;span className=&quot;capitalize&quot;&gt;{meta.label}&lt;/span&gt;
          &lt;/button&gt;
        );
      })}
    &lt;/div&gt;
  );
}

function DeltaBadge({ improvement }: { improvement: number }) {
  const isPositive = improvement &gt; 0;
  const isNeutral = improvement === 0;
  return (
    &lt;span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono font-bold ${
        isPositive
          ? &quot;bg-emerald-500/10 text-emerald-400 border border-emerald-500/20&quot;
          : isNeutral
          ? &quot;bg-gray-500/10 text-gray-400 border border-gray-500/20&quot;
          : &quot;bg-red-500/10 text-red-400 border border-red-500/20&quot;
      }`}
    &gt;
      &lt;TrendingUp className={`w-3 h-3 ${!isPositive &amp;&amp; !isNeutral ? &quot;rotate-180&quot; : &quot;&quot;}`} /&gt;
      {isPositive ? &quot;+&quot; : &quot;&quot;}{improvement.toFixed(2)}
    &lt;/span&gt;
  );
}

function JobStatusBadge({ status }: { status: string }) {
  const config: Record&lt;string, { icon: React.ReactNode; label: string; className: string }&gt; = {
    completed: { icon: &lt;CheckCircle2 className=&quot;w-3.5 h-3.5&quot; /&gt;, label: &quot;Done&quot;, className: &quot;bg-emerald-500/10 text-emerald-400 border-emerald-500/20&quot; },
    failed: { icon: &lt;XCircle className=&quot;w-3.5 h-3.5&quot; /&gt;, label: &quot;Failed&quot;, className: &quot;bg-red-500/10 text-red-400 border-red-500/20&quot; },
    queued: { icon: &lt;Clock className=&quot;w-3.5 h-3.5&quot; /&gt;, label: &quot;Queued&quot;, className: &quot;bg-amber-500/10 text-amber-400 border-amber-500/20&quot; },
    running: { icon: &lt;Loader2 className=&quot;w-3.5 h-3.5 animate-spin&quot; /&gt;, label: &quot;Running&quot;, className: &quot;bg-blue-500/10 text-blue-400 border-blue-500/20&quot; },
    optimizing: { icon: &lt;Loader2 className=&quot;w-3.5 h-3.5 animate-spin&quot; /&gt;, label: &quot;Evolving&quot;, className: &quot;bg-blue-500/10 text-blue-400 border-blue-500/20&quot; },
    evaluating: { icon: &lt;Loader2 className=&quot;w-3.5 h-3.5 animate-spin&quot; /&gt;, label: &quot;Evaluating&quot;, className: &quot;bg-purple-500/10 text-purple-400 border-purple-500/20&quot; },
  };
  const c = config[status] ?? { icon: &lt;Clock className=&quot;w-3.5 h-3.5&quot; /&gt;, label: status, className: &quot;bg-gray-500/10 text-gray-400 border-gray-500/20&quot; };
  return (
    &lt;span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs border ${c.className}`}&gt;
      {c.icon}
      {c.label}
    &lt;/span&gt;
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
  onEvolve: (skillName: string) =&gt; void;
  evolving: boolean;
  runs: EvolutionRun[];
}) {
  const meta = PROVIDER_META[provider] ?? { icon: &quot;🔧&quot;, color: &quot;gray&quot;, label: provider };
  const lastRun = runs
    .filter((r) =&gt; r.skill_name === skill.name)
    .sort((a, b) =&gt; b.timestamp.localeCompare(a.timestamp))[0];

  return (
    &lt;div className=&quot;bg-gray-900/50 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-all group&quot;&gt;
      &lt;div className=&quot;flex items-start justify-between mb-3&quot;&gt;
        &lt;div className=&quot;flex-1 min-w-0&quot;&gt;
          &lt;h3 className=&quot;font-semibold text-white truncate&quot;&gt;{skill.name}&lt;/h3&gt;
          &lt;p className=&quot;text-xs text-gray-500 mt-0.5 line-clamp-1&quot;&gt;
            {skill.description.replace(/^---\s*/, &quot;&quot;).slice(0, 80) || &quot;No description&quot;}
          &lt;/p&gt;
        &lt;/div&gt;
        &lt;span className={`shrink-0 text-xs px-2 py-0.5 rounded-full border ${COLOR_MAP[meta.color]}`}&gt;
          {meta.icon} {meta.label}
        &lt;/span&gt;
      &lt;/div&gt;

      &lt;div className=&quot;flex items-center gap-3 mb-4&quot;&gt;
        {skill.category &amp;&amp; (
          &lt;span className=&quot;text-[10px] uppercase tracking-wider text-gray-600 bg-gray-800/50 px-2 py-0.5 rounded&quot;&gt;
            {skill.category}
          &lt;/span&gt;
        )}
        {lastRun &amp;&amp; &lt;DeltaBadge improvement={lastRun.improvement} /&gt;}
      &lt;/div&gt;

      &lt;button
        onClick={() =&gt; onEvolve(skill.name)}
        disabled={evolving}
        className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
          evolving
            ? &quot;bg-gray-800 text-gray-500 cursor-not-allowed&quot;
            : lastRun
            ? &quot;bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-400 border border-emerald-500/30 hover:from-emerald-500/30 hover:to-teal-500/30&quot;
            : &quot;bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 border border-blue-500/30 hover:from-blue-500/30 hover:to-purple-500/30&quot;
        }`}
      &gt;
        {evolving ? (
          &lt;&gt;
            &lt;Loader2 className=&quot;w-4 h-4 animate-spin&quot; /&gt;
            Evolving...
          &lt;/&gt;
        ) : lastRun ? (
          &lt;&gt;
            &lt;GitCompare className=&quot;w-4 h-4&quot; /&gt;
            Re-Evolve
          &lt;/&gt;
        ) : (
          &lt;&gt;
            &lt;Zap className=&quot;w-4 h-4&quot; /&gt;
            Evolve Now
          &lt;/&gt;
        )}
      &lt;/button&gt;
    &lt;/div&gt;
  );
}

function StatsBar({ stats }: { stats: { totalSkills: number; totalProviders: number; totalRuns: number; avgImprovement: number } }) {
  return (
    &lt;div className=&quot;grid grid-cols-2 md:grid-cols-4 gap-4 mb-8&quot;&gt;
      {[
        { label: &quot;Skills&quot;, value: stats.totalSkills, icon: &lt;Sparkles className=&quot;w-4 h-4&quot; /&gt;, color: &quot;emerald&quot; },
        { label: &quot;Providers&quot;, value: stats.totalProviders, icon: &lt;Zap className=&quot;w-4 h-4&quot; /&gt;, color: &quot;violet&quot; },
        { label: &quot;Evolutions&quot;, value: stats.totalRuns, icon: &lt;History className=&quot;w-4 h-4&quot; /&gt;, color: &quot;blue&quot; },
        { label: &quot;Avg Δ&quot;, value: `${stats.avgImprovement &gt;= 0 ? &quot;+&quot; : &quot;&quot;}${stats.avgImprovement.toFixed(2)}`, icon: &lt;TrendingUp className=&quot;w-4 h-4&quot; /&gt;, color: stats.avgImprovement &gt;= 0 ? &quot;emerald&quot; : &quot;red&quot; },
      ].map((stat) =&gt; (
        &lt;div
          key={stat.label}
          className=&quot;bg-gray-900/50 border border-gray-800 rounded-xl p-4 flex items-center gap-3&quot;
        &gt;
          &lt;div className={`p-2 rounded-lg bg-${stat.color}-500/10 text-${stat.color}-400`}&gt;
            {stat.icon}
          &lt;/div&gt;
          &lt;div&gt;
            &lt;div className=&quot;text-2xl font-bold text-white&quot;&gt;{stat.value}&lt;/div&gt;
            &lt;div className=&quot;text-xs text-gray-500&quot;&gt;{stat.label}&lt;/div&gt;
          &lt;/div&gt;
        &lt;/div&gt;
      ))}
    &lt;/div&gt;
  );
}

// ── Diff Viewer ────────────────────────────────────────────────────
function DiffViewer({ diff, onClose }: { diff: SkillDiff | null; onClose: () =&gt; void }) {
  if (!diff) return null;
  const improvement =
    diff.metrics &amp;&amp; typeof diff.metrics === &quot;object&quot; &amp;&amp; &quot;improvement&quot; in diff.metrics
      ? Number(diff.metrics.improvement)
      : 0;

  return (
    &lt;div className=&quot;fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4&quot;&gt;
      &lt;div className=&quot;bg-gray-950 border border-gray-800 rounded-2xl w-full max-w-5xl max-h-[85vh] overflow-hidden flex flex-col shadow-2xl&quot;&gt;
        {/* Header */}
        &lt;div className=&quot;p-6 border-b border-gray-800 flex items-center justify-between&quot;&gt;
          &lt;div&gt;
            &lt;h2 className=&quot;text-xl font-bold text-white flex items-center gap-3&quot;&gt;
              &lt;GitCompare className=&quot;w-5 h-5 text-emerald-400&quot; /&gt;
              {diff.skill_name}
            &lt;/h2&gt;
            &lt;p className=&quot;text-sm text-gray-500 mt-1&quot;&gt;Before/After Comparison&lt;/p&gt;
          &lt;/div&gt;
          &lt;div className=&quot;flex items-center gap-4&quot;&gt;
            {diff.metrics &amp;&amp; (
              &lt;DeltaBadge improvement={improvement} /&gt;
            )}
            &lt;button
              onClick={onClose}
              className=&quot;p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors&quot;
            &gt;
              ✕
            &lt;/button&gt;
          &lt;/div&gt;
        &lt;/div&gt;

        {/* Metrics summary */}
        {diff.metrics &amp;&amp; typeof diff.metrics === &quot;object&quot; &amp;&amp; (
          &lt;div className=&quot;px-6 py-4 border-b border-gray-800 bg-gray-900/30&quot;&gt;
            &lt;div className=&quot;grid grid-cols-2 md:grid-cols-5 gap-3&quot;&gt;
              {Object.entries(diff.metrics).filter(([k]) =&gt; [&quot;baseline_score&quot;, &quot;evolved_score&quot;, &quot;improvement&quot;, &quot;elapsed_seconds&quot;, &quot;iterations&quot;].includes(k)).map(([key, val]) =&gt; (
                &lt;div key={key} className=&quot;text-center&quot;&gt;
                  &lt;div className=&quot;text-xs text-gray-500 mb-1 capitalize&quot;&gt;{key.replace(/_/g, &quot; &quot;)}&lt;/div&gt;
                  &lt;div className=&quot;text-lg font-mono font-bold text-white&quot;&gt;
                    {key === &quot;elapsed_seconds&quot; ? `${Number(val).toFixed(1)}s` : key === &quot;iterations&quot; ? String(val) : Number(val).toFixed(3)}
                  &lt;/div&gt;
                &lt;/div&gt;
              ))}
            &lt;/div&gt;
          &lt;/div&gt;
        )}

        {/* Side-by-side */}
        &lt;div className=&quot;flex-1 overflow-auto grid grid-cols-2 divide-x divide-gray-800&quot;&gt;
          {/* Baseline */}
          &lt;div className=&quot;p-4&quot;&gt;
            &lt;div className=&quot;flex items-center gap-2 mb-3&quot;&gt;
              &lt;span className=&quot;text-xs font-semibold px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20&quot;&gt;
                BEFORE
              &lt;/span&gt;
              &lt;span className=&quot;text-xs text-gray-500&quot;&gt;
                {diff.baseline ? `${diff.baseline.length} chars` : &quot;N/A&quot;}
              &lt;/span&gt;
            &lt;/div&gt;
            &lt;pre className=&quot;text-xs text-gray-400 whitespace-pre-wrap font-mono leading-relaxed bg-gray-900/50 rounded-lg p-3 border border-gray-800 max-h-[50vh] overflow-auto&quot;&gt;
              {diff.baseline?.slice(0, 5000) || &quot;No baseline available&quot;}
            &lt;/pre&gt;
          &lt;/div&gt;

          {/* Evolved */}
          &lt;div className=&quot;p-4&quot;&gt;
            &lt;div className=&quot;flex items-center gap-2 mb-3&quot;&gt;
              &lt;span className=&quot;text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20&quot;&gt;
                AFTER
              &lt;/span&gt;
              &lt;span className=&quot;text-xs text-gray-500&quot;&gt;
                {diff.evolved ? `${diff.evolved.length} chars` : &quot;N/A&quot;}
              &lt;/span&gt;
              {diff.metrics &amp;&amp; (
                &lt;DeltaBadge improvement={improvement} /&gt;
              )}
            &lt;/div&gt;
            &lt;pre className=&quot;text-xs text-gray-400 whitespace-pre-wrap font-mono leading-relaxed bg-gray-900/50 rounded-lg p-3 border border-gray-800 max-h-[50vh] overflow-auto&quot;&gt;
              {diff.evolved?.slice(0, 5000) || &quot;No evolved version available&quot;}
            &lt;/pre&gt;
          &lt;/div&gt;
        &lt;/div&gt;
      &lt;/div&gt;
    &lt;/div&gt;
  );
}

// ── Main Page ──────────────────────────────────────────────────────
export default function EvolutionHubPage() {
  const [providers, setProviders] = useState&lt;EvolvableProvider[]&gt;([]);
  const [providerNames, setProviderNames] = useState&lt;string[]&gt;([]);
  const [selectedProvider, setSelectedProvider] = useState(&quot;all&quot;);
  const [search, setSearch] = useState(&quot;&quot;);
  const [loading, setLoading] = useState(true);
  const [evolvingSkill, setEvolvingSkill] = useState&lt;string | null&gt;(null);
  const [activeJobId, setActiveJobId] = useState&lt;string | null&gt;(null);
  const [runs, setRuns] = useState&lt;EvolutionRun[]&gt;([]);
  const [selectedDiff, setSelectedDiff] = useState&lt;SkillDiff | null&gt;(null);
  const [error, setError] = useState(&quot;&quot;);

  // ── Data fetching ────────────────────────────────────────────────
  const loadData = useCallback(async () =&gt; {
    try {
      setLoading(true);
      const [evolvableData, runsData] = await Promise.all([
        api&lt;EvolvableResponse&gt;(&quot;/api/evolution/evolvable&quot;),
        fetchEvolutionRuns().catch(() =&gt; [] as EvolutionRun[]),
      ]);

      if (evolvableData.status === &quot;ok&quot;) {
        setProviders(evolvableData.providers);
        setProviderNames(evolvableData.providers.map((p) =&gt; p.provider));
      }
      setRuns(Array.isArray(runsData) ? runsData : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : &quot;Failed to load&quot;);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() =&gt; {
    loadData();
  }, [loadData]);

  // ── Poll active job ──────────────────────────────────────────────
  useEffect(() =&gt; {
    if (!activeJobId) return;
    const interval = setInterval(async () =&gt; {
      try {
        const job = await fetchJob(activeJobId);
        if (job.status === &quot;completed&quot; || job.status === &quot;failed&quot;) {
          setEvolvingSkill(null);
          setActiveJobId(null);
          // Reload runs to show new data
          const runsData = await fetchEvolutionRuns().catch(() =&gt; [] as EvolutionRun[]);
          setRuns(Array.isArray(runsData) ? runsData : []);
        }
      } catch {
        // ignore poll errors
      }
    }, 2000);
    return () =&gt; clearInterval(interval);
  }, [activeJobId]);

  // ── Actions ──────────────────────────────────────────────────────
  const handleEvolve = async (skillName: string) =&gt; {
    try {
      setEvolvingSkill(skillName);
      setError(&quot;&quot;);
      const result = await startEvolution(skillName, 3);
      if (result.error) {
        setError(result.error);
        setEvolvingSkill(null);
      } else {
        setActiveJobId(result.job_id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : &quot;Evolution failed to start&quot;);
      setEvolvingSkill(null);
    }
  };

  const handleViewDiff = async (skillName: string, runDir?: string) =&gt; {
    try {
      // Find the run directory from runs
      const run = runs.find((r) =&gt; r.skill_name === skillName);
      if (!run) return;

      // Fetch diff
      const diffData = await fetchSkillDiff(skillName, &quot;latest&quot;);
      setSelectedDiff(diffData);
    } catch (e) {
      setError(e instanceof Error ? e.message : &quot;Failed to load diff&quot;);
    }
  };

  // ── Filtering ────────────────────────────────────────────────────
  const filteredSkills = providers
    .filter((p) =&gt; selectedProvider === &quot;all&quot; || p.provider === selectedProvider)
    .flatMap((p) =&gt;
      p.skills
        .filter((s) =&gt; {
          const q = search.toLowerCase();
          return (
            !q ||
            s.name.toLowerCase().includes(q) ||
            s.description.toLowerCase().includes(q) ||
            s.category?.toLowerCase().includes(q)
          );
        })
        .map((s) =&gt; ({ ...s, _provider: p.provider }))
    );

  // ── Stats ────────────────────────────────────────────────────────
  const stats = {
    totalSkills: providers.reduce((acc, p) =&gt; acc + p.skills.length, 0),
    totalProviders: providers.length,
    totalRuns: runs.length,
    avgImprovement:
      runs.length &gt; 0
        ? runs.reduce((acc, r) =&gt; acc + (r.improvement || 0), 0) / runs.length
        : 0,
  };

  // ── Render ───────────────────────────────────────────────────────
  return (
    &lt;div className=&quot;min-h-screen px-6 py-8 max-w-7xl mx-auto&quot;&gt;
      {/* Header */}
      &lt;div className=&quot;mb-8&quot;&gt;
        &lt;h1 className=&quot;text-4xl font-bold text-white flex items-center gap-3 mb-2&quot;&gt;
          &lt;Sparkles className=&quot;w-8 h-8 text-emerald-400&quot; /&gt;
          Evolution Hub
        &lt;/h1&gt;
        &lt;p className=&quot;text-gray-500 text-lg&quot;&gt;
          Multi-provider AI skill evolution — Hermes · Claude Code · OpenCode · Kilocode
        &lt;/p&gt;
      &lt;/div&gt;

      {/* Error banner */}
      {error &amp;&amp; (
        &lt;div className=&quot;mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400&quot;&gt;
          &lt;AlertTriangle className=&quot;w-5 h-5 shrink-0&quot; /&gt;
          &lt;span className=&quot;text-sm&quot;&gt;{error}&lt;/span&gt;
          &lt;button onClick={() =&gt; setError(&quot;&quot;)} className=&quot;ml-auto text-red-400 hover:text-red-300&quot;&gt;
            ✕
          &lt;/button&gt;
        &lt;/div&gt;
      )}

      {/* Stats */}
      {!loading &amp;&amp; &lt;StatsBar stats={stats} /&gt;}

      {/* Filters */}
      {!loading &amp;&amp; (
        &lt;&gt;
          &lt;ProviderTabs
            providers={providerNames}
            selected={selectedProvider}
            onSelect={setSelectedProvider}
          /&gt;
          &lt;div className=&quot;relative mb-6&quot;&gt;
            &lt;input
              type=&quot;text&quot;
              value={search}
              onChange={(e) =&gt; setSearch(e.target.value)}
              placeholder=&quot;Search skills...&quot;
              className=&quot;w-full p-3 bg-gray-900 border border-gray-800 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500/50 transition-colors&quot;
            /&gt;
          &lt;/div&gt;
        &lt;/&gt;
      )}

      {/* Loading */}
      {loading &amp;&amp; (
        &lt;div className=&quot;flex items-center justify-center py-20&quot;&gt;
          &lt;Loader2 className=&quot;w-8 h-8 animate-spin text-emerald-400&quot; /&gt;
        &lt;/div&gt;
      )}

      {/* Skill Grid */}
      {!loading &amp;&amp; (
        &lt;div className=&quot;grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-12&quot;&gt;
          {filteredSkills.map((skill) =&gt; (
            &lt;SkillCard
              key={`${skill._provider}-${skill.name}`}
              skill={skill}
              provider={skill._provider}
              onEvolve={handleEvolve}
              evolving={evolvingSkill === skill.name}
              runs={runs}
            /&gt;
          ))}
          {filteredSkills.length === 0 &amp;&amp; (
            &lt;div className=&quot;col-span-full text-center py-16 text-gray-600&quot;&gt;
              &lt;Sparkles className=&quot;w-12 h-12 mx-auto mb-4 opacity-30&quot; /&gt;
              &lt;p className=&quot;text-lg&quot;&gt;No skills found&lt;/p&gt;
              &lt;p className=&quot;text-sm mt-1&quot;&gt;Try a different filter or search term&lt;/p&gt;
            &lt;/div&gt;
          )}
        &lt;/div&gt;
      )}

      {/* Evolution History */}
      {!loading &amp;&amp; runs.length &gt; 0 &amp;&amp; (
        &lt;div className=&quot;mb-12&quot;&gt;
          &lt;h2 className=&quot;text-2xl font-bold text-white flex items-center gap-2 mb-4&quot;&gt;
            &lt;History className=&quot;w-5 h-5 text-blue-400&quot; /&gt;
            Evolution History
          &lt;/h2&gt;
          &lt;div className=&quot;bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden&quot;&gt;
            &lt;div className=&quot;overflow-x-auto&quot;&gt;
              &lt;table className=&quot;w-full text-sm&quot;&gt;
                &lt;thead&gt;
                  &lt;tr className=&quot;border-b border-gray-800 text-left&quot;&gt;
                    &lt;th className=&quot;p-4 text-gray-500 font-medium&quot;&gt;Skill&lt;/th&gt;
                    &lt;th className=&quot;p-4 text-gray-500 font-medium&quot;&gt;Date&lt;/th&gt;
                    &lt;th className=&quot;p-4 text-gray-500 font-medium&quot;&gt;Baseline&lt;/th&gt;
                    &lt;th className=&quot;p-4 text-gray-500 font-medium&quot;&gt;Evolved&lt;/th&gt;
                    &lt;th className=&quot;p-4 text-gray-500 font-medium&quot;&gt;Δ Delta&lt;/th&gt;
                    &lt;th className=&quot;p-4 text-gray-500 font-medium&quot;&gt;Time&lt;/th&gt;
                    &lt;th className=&quot;p-4 text-gray-500 font-medium&quot;&gt;Status&lt;/th&gt;
                    &lt;th className=&quot;p-4 text-gray-500 font-medium&quot;&gt;Actions&lt;/th&gt;
                  &lt;/tr&gt;
                &lt;/thead&gt;
                &lt;tbody&gt;
                  {runs.slice(0, 50).map((run, i) =&gt; (
                    &lt;tr key={i} className=&quot;border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors&quot;&gt;
                      &lt;td className=&quot;p-4 font-medium text-white&quot;&gt;{run.skill_name}&lt;/td&gt;
                      &lt;td className=&quot;p-4 text-gray-400 font-mono text-xs&quot;&gt;
                        {run.timestamp.slice(0, 10)}
                      &lt;/td&gt;
                      &lt;td className=&quot;p-4 font-mono text-gray-400&quot;&gt;
                        {(run.baseline_score ?? 0).toFixed(3)}
                      &lt;/td&gt;
                      &lt;td className=&quot;p-4 font-mono text-gray-400&quot;&gt;
                        {(run.evolved_score ?? 0).toFixed(3)}
                      &lt;/td&gt;
                      &lt;td className=&quot;p-4&quot;&gt;
                        &lt;DeltaBadge improvement={run.improvement ?? 0} /&gt;
                      &lt;/td&gt;
                      &lt;td className=&quot;p-4 text-gray-500 font-mono text-xs&quot;&gt;
                        {(run.elapsed_seconds ?? 0).toFixed(1)}s
                      &lt;/td&gt;
                      &lt;td className=&quot;p-4&quot;&gt;
                        {run.constraints_passed !== undefined ? (
                          run.constraints_passed ? (
                            &lt;span className=&quot;text-emerald-400 text-xs font-medium&quot;&gt;✓ Pass&lt;/span&gt;
                          ) : (
                            &lt;span className=&quot;text-amber-400 text-xs font-medium&quot;&gt;⚠ Issues&lt;/span&gt;
                          )
                        ) : (
                          &lt;span className=&quot;text-gray-600&quot;&gt;—&lt;/span&gt;
                        )}
                      &lt;/td&gt;
                      &lt;td className=&quot;p-4&quot;&gt;
                        &lt;button
                          onClick={() =&gt; handleViewDiff(run.skill_name)}
                          className=&quot;text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1&quot;
                        &gt;
                          &lt;GitCompare className=&quot;w-3 h-3&quot; /&gt;
                          Compare
                        &lt;/button&gt;
                      &lt;/td&gt;
                    &lt;/tr&gt;
                  ))}
                &lt;/tbody&gt;
              &lt;/table&gt;
            &lt;/div&gt;
          &lt;/div&gt;
        &lt;/div&gt;
      )}

      {/* Diff Viewer Modal */}
      &lt;DiffViewer diff={selectedDiff} onClose={() =&gt; setSelectedDiff(null)} /&gt;
    &lt;/div&gt;
  );
}

---

&quot;use client&quot;;

import { useState } from &quot;react&quot;;
import dynamic from &quot;next/dynamic&quot;;
import AppSidebar from &quot;@/components/Sidebar&quot;;
import type { Page } from &quot;@/components/Sidebar&quot;;
import { AnimatedThemeToggler } from &quot;@/components/ui/animated-theme-toggler&quot;;

// Lazy load page components
const OverviewPage = dynamic(() =&gt; import(&quot;@/components/pages/OverviewPage&quot;), {
  loading: () =&gt; &lt;PageLoader label=&quot;Overview&quot; /&gt;,
});
const SkillStudioPage = dynamic(() =&gt; import(&quot;@/components/pages/SkillStudioPage&quot;), {
  loading: () =&gt; &lt;PageLoader label=&quot;Skill Studio&quot; /&gt;,
});
const EvolutionPage = dynamic(() =&gt; import(&quot;@/components/pages/EvolutionPage&quot;), {
  loading: () =&gt; &lt;PageLoader label=&quot;Evolution&quot; /&gt;,
});
const DatasetPage = dynamic(() =&gt; import(&quot;@/components/pages/DatasetPage&quot;), {
  loading: () =&gt; &lt;PageLoader label=&quot;Datasets&quot; /&gt;,
});
const MetricsPage = dynamic(() =&gt; import(&quot;@/components/pages/MetricsPage&quot;), {
  loading: () =&gt; &lt;PageLoader label=&quot;Metrics&quot; /&gt;,
});
const LogsPage = dynamic(() =&gt; import(&quot;@/components/pages/LogsPage&quot;), {
  loading: () =&gt; &lt;PageLoader label=&quot;Logs&quot; /&gt;,
});
const SettingsPage = dynamic(() =&gt; import(&quot;@/components/pages/SettingsPage&quot;), {
  loading: () =&gt; &lt;PageLoader label=&quot;Settings&quot; /&gt;,
});
const CuratorPage = dynamic(() =&gt; import(&quot;@/components/pages/CuratorPage&quot;), {
  loading: () =&gt; &lt;PageLoader label=&quot;Curator&quot; /&gt;,
});

function PageLoader({ label }: { label: string }) {
  return (
    &lt;div className=&quot;min-h-[20rem] flex items-center justify-center&quot;&gt;
      &lt;p className=&quot;text-sm text-muted-foreground animate-pulse&quot;&gt;
        Cargando {label}...
      &lt;/p&gt;
    &lt;/div&gt;
  );
}

const pages: Record&lt;Page, React.ComponentType&gt; = {
  overview: OverviewPage,
  skills: SkillStudioPage,
  evolution: EvolutionPage,
  datasets: DatasetPage,
  metrics: MetricsPage,
  logs: LogsPage,
  settings: SettingsPage,
  curator: CuratorPage,
};

export default function Home() {
  const [activePage, setActivePage] = useState&lt;Page&gt;(&quot;overview&quot;);
  const PageComponent = pages[activePage];

  return (
    &lt;AppSidebar activePage={activePage} onNavigate={setActivePage}&gt;
      {/* Fixed theme toggler — top right corner */}
      &lt;AnimatedThemeToggler
        className=&quot;fixed top-4 right-4 z-50 p-2.5 rounded-full bg-card border border-border shadow-md hover:shadow-lg hover:bg-accent transition-all duration-200 text-foreground&quot;
        duration={400}
      /&gt;
      &lt;PageComponent /&gt;
    &lt;/AppSidebar&gt;
  );
}

---


&quot;use client&quot;;
import { api, fetchSkillProviders } from &apos;@/lib/api&apos;;

import { useState, useEffect } from &quot;react&quot;;
import { Sparkles, ToggleLeft, ToggleRight, Search, RefreshCw } from &quot;lucide-react&quot;;

interface Skill {
  name: string;
  description: string;
  enabled: boolean;
  tags: string[];
  is_fork?: boolean;
  category?: string;
}

interface Provider {
  name: string;
  total: number;
  enabled: number;
  skills: Skill[];
  path?: string;
}

export default function SkillsPage() {
  const [providers, setProviders] = useState&lt;Provider[]&gt;([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(&quot;&quot;);
  const [filterProvider, setFilterProvider] = useState&lt;string&gt;(&quot;all&quot;);
  const [filterStatus, setFilterStatus] = useState&lt;string&gt;(&quot;all&quot;);
  const [deleteTarget, setDeleteTarget] = useState&lt;{provider: string, skill: string} | null&gt;(null);

  const fetchSkills = async () =&gt; {
    setLoading(true);
    try {
      const data = await fetchSkillProviders();
      if (data.status === &quot;ok&quot;) {
        setProviders(data.providers);
      }
    } catch (error) {
      console.error(&quot;Error fetching skills:&quot;, error);
    }
    setLoading(false);
  };

  useEffect(() =&gt; {
    fetchSkills();
  }, []);


  const handleDeleteSkill = async (provider: string, skillName: string, isGlobal: boolean = false) =&gt; {
    if (!confirm(`¿Eliminar ${isGlobal ? &quot;GLOBALMENTE&quot; : &quot;de &quot;+provider} la skill &quot;${skillName}&quot;?`)) return;
    
    try {
      const endpoint = isGlobal 
        ? `/api/skills/global/${encodeURIComponent(skillName)}`
        : `/api/skills/${provider}/${encodeURIComponent(skillName)}`;
      
      const res = await api&lt;{status:string; message?:string}&gt;(endpoint, {
        method: &quot;DELETE&quot;,
      });
      
      if (res.status === &quot;ok&quot;) {
        fetchSkills();
      } else {
        alert(&quot;Error: &quot; + (res.message || &quot;unknown&quot;));
      }
    } catch (error) {
      console.error(&quot;Delete error:&quot;, error);
      alert(&quot;Error eliminando skill&quot;);
    }
  };

  const toggleSkill = async (provider: string, skillName: string, enabled: boolean) =&gt; {
    try {
      await api&lt;{status:string}&gt;(&quot;/api/skills/toggle&quot;, {
        method: &quot;POST&quot;,
        headers: { &quot;Content-Type&quot;: &quot;application/json&quot; },
        body: JSON.stringify({ provider, skill_name: skillName, enabled }),
      });
      // Actualizar localmente
      setProviders(prev =&gt; prev.map(p =&gt; {
        if (p.name !== provider) return p;
        return {
          ...p,
          skills: p.skills.map(s =&gt;
            s.name === skillName ? { ...s, enabled } : s
          ),
          enabled: p.skills.filter(s =&gt;
            (s.name === skillName ? enabled : s.enabled)
          ).length,
        };
      }));
    } catch (error) {
      console.error(&quot;Error toggling skill:&quot;, error);
    }
  };

  const [filterCategory, setFilterCategory] = useState&lt;string&gt;(&quot;all&quot;);

  // Extraer categorías únicas
  const allCategories = Array.from(
    new Set(providers.flatMap(p =&gt; p.skills.map(s =&gt; s.category)))
  ).sort();

  // Filtrar skills por búsqueda y categoría
  const filteredProviders = providers.map(p =&gt; ({
    ...p,
    skills: p.skills.filter(s =&gt; {
      const q = search.toLowerCase();
      const matchText = 
        s.name.toLowerCase().includes(q) ||
        s.description.toLowerCase().includes(q);
      const matchProvider = filterProvider === &quot;all&quot; || p.name === filterProvider;
      const matchStatus = filterStatus === &quot;all&quot; || 
        (filterStatus === &quot;enabled&quot; &amp;&amp; s.enabled) ||
        (filterStatus === &quot;disabled&quot; &amp;&amp; !s.enabled);
      const matchCategory = filterCategory === &quot;all&quot; || s.category === filterCategory;
      return matchText &amp;&amp; matchProvider &amp;&amp; matchStatus &amp;&amp; matchCategory;
    }),
  })).filter(p =&gt; p.skills.length &gt; 0);

  const providerIcons: Record&lt;string, string&gt; = {
    &quot;claude-code&quot;: &quot;🤖&quot;,
    &quot;opencode&quot;: &quot;💻&quot;,
    &quot;kilocode&quot;: &quot;⚡&quot;,
    &quot;antigravity&quot;: &quot;🚀&quot;,
    &quot;hermes&quot;: &quot;🪽&quot;,
  };

  const providerColors: Record&lt;string, string&gt; = {
    &quot;claude-code&quot;: &quot;bg-orange-500/10 border-orange-500/30 text-orange-400&quot;,
    &quot;opencode&quot;: &quot;bg-blue-500/10 border-blue-500/30 text-blue-400&quot;,
    &quot;kilocode&quot;: &quot;bg-yellow-500/10 border-yellow-500/30 text-yellow-400&quot;,
    &quot;antigravity&quot;: &quot;bg-purple-500/10 border-purple-500/30 text-purple-400&quot;,
    &quot;hermes&quot;: &quot;bg-emerald-500/10 border-emerald-500/30 text-emerald-400&quot;,
  };

  return (
    &lt;div className=&quot;min-h-screen bg-gray-950 text-gray-100 p-6&quot;&gt;
      &lt;div className=&quot;max-w-6xl mx-auto&quot;&gt;
        {/* Header */}
        &lt;div className=&quot;flex items-center justify-between mb-8&quot;&gt;
          &lt;div className=&quot;flex items-center gap-3&quot;&gt;
            &lt;Sparkles className=&quot;w-8 h-8 text-purple-400&quot; /&gt;
            &lt;div&gt;
              &lt;h1 className=&quot;text-3xl font-bold&quot;&gt;Skill Hub&lt;/h1&gt;
              &lt;p className=&quot;text-gray-400 text-sm&quot;&gt;
                Gestiona tus skills de todos los proveedores
              &lt;/p&gt;
            &lt;/div&gt;
          &lt;/div&gt;
          &lt;button
            onClick={fetchSkills}
            disabled={loading}
            className=&quot;flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors&quot;
          &gt;
            &lt;RefreshCw className={`w-4 h-4 ${loading ? &quot;animate-spin&quot; : &quot;&quot;}`} /&gt;
            Refresh
          &lt;/button&gt;
        &lt;/div&gt;

        {/* Search &amp; Filters */}
        &lt;div className=&quot;relative mb-6&quot;&gt;
          &lt;Search className=&quot;absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500&quot; /&gt;
          &lt;input
            type=&quot;text&quot;
            placeholder=&quot;Buscar skills por nombre, proveedor o descripción...&quot;
            value={search}
            onChange={(e) =&gt; setSearch(e.target.value)}
            className=&quot;w-full pl-10 pr-4 py-3 bg-gray-900 border border-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500&quot;
          /&gt;
        &lt;/div&gt;

        {/* Category &amp; Provider Filters */}
        &lt;div className=&quot;flex flex-wrap gap-3 mb-6&quot;&gt;
          &lt;select
            value={filterCategory}
            onChange={(e) =&gt; setFilterCategory(e.target.value)}
            className=&quot;px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500&quot;
          &gt;
            &lt;option value=&quot;all&quot;&gt;📁 Todas las categorías&lt;/option&gt;
            {allCategories.map(cat =&gt; (
              &lt;option key={cat} value={cat}&gt;{cat}&lt;/option&gt;
            ))}
          &lt;/select&gt;
          
          &lt;select
            value={filterProvider}
            onChange={(e) =&gt; setFilterProvider(e.target.value)}
            className=&quot;px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500&quot;
          &gt;
            &lt;option value=&quot;all&quot;&gt;🔧 Todos los providers&lt;/option&gt;
            {providers.map(p =&gt; (
              &lt;option key={p.name} value={p.name}&gt;{p.name}&lt;/option&gt;
            ))}
          &lt;/select&gt;

          &lt;select
            value={filterStatus}
            onChange={(e) =&gt; setFilterStatus(e.target.value)}
            className=&quot;px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500&quot;
          &gt;
            &lt;option value=&quot;all&quot;&gt;⚡ Todos los estados&lt;/option&gt;
            &lt;option value=&quot;enabled&quot;&gt;✅ Activas&lt;/option&gt;
            &lt;option value=&quot;disabled&quot;&gt;❌ Desactivadas&lt;/option&gt;
          &lt;/select&gt;

          {(filterCategory !== &quot;all&quot; || filterProvider !== &quot;all&quot; || filterStatus !== &quot;all&quot; || search) &amp;&amp; (
            &lt;button
              onClick={() =&gt; { setFilterCategory(&quot;all&quot;); setFilterProvider(&quot;all&quot;); setFilterStatus(&quot;all&quot;); setSearch(&quot;&quot;); }}
              className=&quot;px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-400 transition-colors&quot;
            &gt;
              Limpiar filtros
            &lt;/button&gt;
          )}
        &lt;/div&gt;

        {/* Stats */}
        {!loading &amp;&amp; (
          &lt;div className=&quot;grid grid-cols-2 md:grid-cols-5 gap-4 mb-8&quot;&gt;
            {providers.map(p =&gt; (
              &lt;div
                key={p.name}
                className={`p-4 rounded-lg border ${providerColors[p.name] || &quot;bg-gray-800 border-gray-700&quot;}`}
              &gt;
                &lt;div className=&quot;text-2xl mb-1&quot;&gt;{providerIcons[p.name] || &quot;🔧&quot;}&lt;/div&gt;
                &lt;div className=&quot;text-sm font-medium capitalize&quot;&gt;{p.name}&lt;/div&gt;
                &lt;div className=&quot;text-2xl font-bold&quot;&gt;{p.enabled}/{p.total}&lt;/div&gt;
                &lt;div className=&quot;text-xs opacity-70&quot;&gt;habilitadas&lt;/div&gt;
              &lt;/div&gt;
            ))}
          &lt;/div&gt;
        )}

        {/* Skills por proveedor */}
        {loading ? (
          &lt;div className=&quot;flex items-center justify-center py-12&quot;&gt;
            &lt;RefreshCw className=&quot;w-8 h-8 animate-spin text-purple-400&quot; /&gt;
            &lt;span className=&quot;ml-3&quot;&gt;Escaneando skills...&lt;/span&gt;
          &lt;/div&gt;
        ) : (
          &lt;div className=&quot;space-y-8&quot;&gt;
            {filteredProviders.map(provider =&gt; (
              &lt;div key={provider.name} className=&quot;bg-gray-900/50 rounded-xl border border-gray-800 p-6&quot;&gt;
                &lt;div className=&quot;flex items-center justify-between mb-4&quot;&gt;
                  &lt;div className=&quot;flex items-center gap-3&quot;&gt;
                    &lt;span className=&quot;text-3xl&quot;&gt;{providerIcons[provider.name] || &quot;🔧&quot;}&lt;/span&gt;
                    &lt;div&gt;
                      &lt;h2 className=&quot;text-xl font-bold capitalize flex items-center gap-2&quot;&gt;
                        {provider.name}
                        &lt;span className=&quot;text-sm font-normal text-gray-500&quot;&gt;
                          ({provider.enabled}/{provider.total} activas)
                        &lt;/span&gt;
                      &lt;/h2&gt;
                    &lt;/div&gt;
                  &lt;/div&gt;
                  &lt;div className=&quot;flex items-center gap-2&quot;&gt;
                    &lt;span className=&quot;px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-800 text-gray-400 border border-gray-700&quot;&gt;
                      {provider.total} skills
                    &lt;/span&gt;
                  &lt;/div&gt;
                &lt;/div&gt;

                &lt;div className=&quot;grid gap-3 md:grid-cols-2&quot;&gt;
                  {provider.skills
                    .filter(skill =&gt; {
                      const q = search.toLowerCase();
                      const matchText = 
                        skill.name.toLowerCase().includes(q) ||
                        skill.description.toLowerCase().includes(q) ||
                        skill.tags.some(t =&gt; t.toLowerCase().includes(q));
                      const matchProvider = filterProvider === &quot;all&quot; || provider.name === filterProvider;
                      const matchStatus = filterStatus === &quot;all&quot; || 
                        (filterStatus === &quot;enabled&quot; &amp;&amp; skill.enabled) ||
                        (filterStatus === &quot;disabled&quot; &amp;&amp; !skill.enabled);
                      return matchText &amp;&amp; matchProvider &amp;&amp; matchStatus;
                    })
                    .map(skill =&gt; (
                    &lt;div
                      key={`${provider.name}-${skill.name}`}
                      className=&quot;p-4 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-gray-600 transition-colors&quot;
                    &gt;
                      &lt;div className=&quot;flex items-start justify-between gap-4&quot;&gt;
                        &lt;div className=&quot;flex-1 min-w-0&quot;&gt;
                          &lt;div className=&quot;flex items-center gap-2 mb-1&quot;&gt;
                            &lt;h3 className=&quot;font-medium text-gray-100 truncate&quot;&gt;
                              {skill.name}
                            &lt;/h3&gt;
                            {skill.is_fork &amp;&amp; (
                              &lt;span className=&quot;px-1.5 py-0.5 text-xs bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 rounded&quot;&gt;
                                FORK
                              &lt;/span&gt;
                            )}
                          &lt;/div&gt;
                          &lt;p className=&quot;text-sm text-gray-400 line-clamp-2&quot;&gt;
                            {skill.description}
                          &lt;/p&gt;
                          {skill.tags.length &gt; 0 &amp;&amp; (
                            &lt;div className=&quot;flex gap-1 mt-2 flex-wrap&quot;&gt;
                              {skill.tags.slice(0, 4).map(tag =&gt; (
                                &lt;span key={tag} className=&quot;px-2 py-0.5 text-xs bg-gray-700 text-gray-300 rounded&quot;&gt;
                                  {tag}
                                &lt;/span&gt;
                              ))}
                              {skill.tags.length &gt; 4 &amp;&amp; (
                                &lt;span className=&quot;px-2 py-0.5 text-xs bg-gray-700 text-gray-300 rounded&quot;&gt;
                                  +{skill.tags.length - 4}
                                &lt;/span&gt;
                              )}
                            &lt;/div&gt;
                          )}
                        &lt;/div&gt;
                        &lt;div className=&quot;flex items-center gap-2 flex-wrap&quot;&gt;
                          &lt;button
                            onClick={() =&gt; toggleSkill(provider.name, skill.name, !skill.enabled)}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                              skill.enabled
                                ? &quot;bg-green-500/10 text-green-400 border border-green-500/20 hover:bg-green-500/20&quot;
                                : &quot;bg-gray-700 text-gray-300 border border-gray-600 hover:bg-gray-600&quot;
                            }`}
                            title={skill.enabled ? &quot;Desactivar&quot; : &quot;Activar&quot;}
                          &gt;
                            {skill.enabled ? (
                              &lt;&gt;&lt;ToggleRight className=&quot;w-4 h-4&quot; /&gt; Activada&lt;/&gt;
                            ) : (
                              &lt;&gt;&lt;ToggleLeft className=&quot;w-4 h-4&quot; /&gt; Desactivada&lt;/&gt;
                            )}
                          &lt;/button&gt;
                          &lt;button
                            onClick={() =&gt; handleDeleteSkill(provider.name, skill.name, false)}
                            className=&quot;px-3 py-1.5 rounded-lg text-sm font-medium bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors&quot;
                            title=&quot;Eliminar de este provider&quot;
                          &gt;
                            🗑️ Quitar
                          &lt;/button&gt;
                          {!skill.is_fork &amp;&amp; (
                            &lt;button
                              onClick={() =&gt; handleDeleteSkill(provider.name, skill.name, true)}
                              className=&quot;px-3 py-1.5 rounded-lg text-sm font-medium bg-orange-500/10 text-orange-400 border border-orange-500/20 hover:bg-orange-500/20 transition-colors&quot;
                              title=&quot;Eliminar skill globalmente&quot;
                            &gt;
                              🗑️💥 Eliminar Global
                            &lt;/button&gt;
                          )}
                        &lt;/div&gt;
                      &lt;/div&gt;
                    &lt;/div&gt;
                  ))}
                &lt;/div&gt;
              &lt;/div&gt;
            ))}
            {!loading &amp;&amp; filteredProviders.length === 0 ? (
              &lt;div className=&quot;text-center py-12 text-gray-500&quot;&gt;
                No se encontraron skills. Instala skills en los directorios:
                &lt;pre className=&quot;mt-2 p-4 bg-gray-900 rounded text-xs text-left overflow-auto&quot;&gt;
                  {`~/.claude/skills/
~/.opencode/skills/
~/.kilocode/skills/
~/.antigravity/providers/
~/.hermes/skills/`}
                &lt;/pre&gt;
              &lt;/div&gt;
            ) : null}
          &lt;/div&gt;
        )}
      &lt;/div&gt;
    &lt;/div&gt;
  );
}

    
