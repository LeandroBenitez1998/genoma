---
title: Page
summary: Source file app/evolution/page.tsx in the Next.js frontend
tags: []
related: []
keywords: []
createdAt: '2026-05-21T07:39:26.008Z'
updatedAt: '2026-05-21T07:39:26.008Z'
---
## Reason
Curate app/evolution/page.tsx from src folder

## Raw Concept
**Task:**
Document app/evolution/page.tsx

**Timestamp:** 2026-05-21

## Narrative
### Structure
Implementation for app/evolution/page.tsx

### Highlights
Captured complete source content from app/evolution/page.tsx

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

    
