---
title: SettingsPage
summary: ''
tags: []
related: []
keywords: []
createdAt: '2026-04-28T01:33:30.556Z'
updatedAt: '2026-04-28T01:33:30.556Z'
---
## Reason
Preserving complete src/components/pages/SettingsPage.tsx from hermes-dashboard project

## Raw Concept
**Task:**
Preserve src/components/pages/SettingsPage.tsx

**Files:**
- src/components/pages/SettingsPage.tsx

**Timestamp:** 2026-04-28

**Patterns:**
- `SettingsPage` - Component or function

## Narrative
### Structure
TSX file with 1 components/functions

### Highlights
Source: hermes-dashboard/src/components/pages/SettingsPage.tsx

---


&quot;use client&quot;;

import { useState, useEffect } from &quot;react&quot;;
import { motion } from &quot;framer-motion&quot;;
import {
  Settings,
  Key,
  Eye,
  EyeOff,
  Check,
  X,
  Server,
  FolderOpen,
} from &quot;lucide-react&quot;;
import { fetchHealth } from &quot;@/lib/api&quot;;

interface EnvVar {
  key: string;
  value: string;
  desc: string;
}

export default function SettingsPage() {
  const [health, setHealth] = useState&lt;{
    status: string;
    hermes_repo: string;
    hermes_repo_exists: boolean;
    evolution_dir: string;
    evolution_dir_exists: boolean;
    skills_count: number;
  } | null&gt;(null);

  const [showKeys, setShowKeys] = useState&lt;Record&lt;string, boolean&gt;&gt;({});

  useEffect(() =&gt; {
    fetchHealth().then(setHealth).catch(() =&gt; {});
  }, []);

  const envVars: EnvVar[] = [
    { key: &quot;OPENAI_API_KEY&quot;, value: &quot;sk-...&quot;, desc: &quot;Used by DSPy for LLM calls&quot; },
    { key: &quot;OPENAI_BASE_URL&quot;, value: &quot;http://localhost:11434/v1&quot;, desc: &quot;Ollama endpoint&quot; },
    { key: &quot;HERMES_AGENT_REPO&quot;, value: health?.hermes_repo || &quot;~/.hermes/hermes-agent&quot;, desc: &quot;Path to hermes-agent repo&quot; },
  ];

  return (
    &lt;div className=&quot;space-y-6 max-w-3xl&quot;&gt;
      {/* System Paths */}
      &lt;motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className=&quot;glass-card rounded-2xl p-6&quot;&gt;
        &lt;h2 className=&quot;text-sm font-semibold uppercase tracking-wider flex items-center gap-2 mb-4&quot;&gt;&lt;Server className=&quot;w-4 h-4 text-accent-cyan&quot; /&gt;System Paths&lt;/h2&gt;
        {health &amp;&amp; (
          &lt;div className=&quot;space-y-3&quot;&gt;
            {[
              { label: &quot;Hermes Agent Repo&quot;, path: health.hermes_repo, exists: health.hermes_repo_exists },
              { label: &quot;Evolution Engine&quot;, path: health.evolution_dir, exists: health.evolution_dir_exists },
            ].map((item) =&gt; (
              &lt;div key={item.label} className=&quot;flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]&quot;&gt;
                &lt;div className=&quot;flex items-center gap-3&quot;&gt;&lt;FolderOpen className=&quot;w-4 h-4 text-muted-foreground&quot; /&gt;&lt;div&gt;&lt;p className=&quot;text-sm font-medium&quot;&gt;{item.label}&lt;/p&gt;&lt;p className=&quot;text-[10px] font-mono text-muted-foreground&quot;&gt;{item.path}&lt;/p&gt;&lt;/div&gt;&lt;/div&gt;
                {item.exists ? &lt;Check className=&quot;w-4 h-4 text-success&quot; /&gt; : &lt;X className=&quot;w-4 h-4 text-error&quot; /&gt;}
              &lt;/div&gt;
            ))}
            &lt;div className=&quot;flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]&quot;&gt;
              &lt;div className=&quot;flex items-center gap-3&quot;&gt;&lt;FolderOpen className=&quot;w-4 h-4 text-muted-foreground&quot; /&gt;&lt;div&gt;&lt;p className=&quot;text-sm font-medium&quot;&gt;Skills Found&lt;/p&gt;&lt;/div&gt;&lt;/div&gt;
              &lt;span className=&quot;text-sm font-mono text-accent-violet&quot;&gt;{health.skills_count}&lt;/span&gt;
            &lt;/div&gt;
          &lt;/div&gt;
        )}
      &lt;/motion.div&gt;

      {/* Environment Variables */}
      &lt;motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className=&quot;glass-card rounded-2xl p-6&quot;&gt;
        &lt;h2 className=&quot;text-sm font-semibold uppercase tracking-wider flex items-center gap-2 mb-4&quot;&gt;&lt;Key className=&quot;w-4 h-4 text-accent-violet&quot; /&gt;Environment Variables&lt;/h2&gt;
        &lt;div className=&quot;space-y-3&quot;&gt;
          {envVars.map((env) =&gt; (
            &lt;div key={env.key} className=&quot;p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]&quot;&gt;
              &lt;div className=&quot;flex items-center justify-between mb-1&quot;&gt;
                &lt;span className=&quot;text-xs font-mono text-accent-cyan&quot;&gt;{env.key}&lt;/span&gt;
                &lt;button onClick={() =&gt; setShowKeys((prev) =&gt; ({ ...prev, [env.key]: !prev[env.key] }))} className=&quot;text-muted-foreground/50 hover:text-muted-foreground&quot;&gt;{showKeys[env.key] ? &lt;EyeOff className=&quot;w-3 h-3&quot; /&gt; : &lt;Eye className=&quot;w-3 h-3&quot; /&gt;}&lt;/button&gt;
              &lt;/div&gt;
              &lt;p className=&quot;text-xs font-mono text-muted-foreground&quot;&gt;{showKeys[env.key] ? env.value : &quot;••••••••••••&quot;}&lt;/p&gt;
              &lt;p className=&quot;text-[10px] text-muted-foreground/50 mt-1&quot;&gt;{env.desc}&lt;/p&gt;
            &lt;/div&gt;
          ))}
        &lt;/div&gt;
        &lt;p className=&quot;text-[10px] text-muted-foreground/40 mt-4&quot;&gt;Set these in your shell or .env file. The backend reads them on startup.&lt;/p&gt;
      &lt;/motion.div&gt;
    &lt;/div&gt;
  );
}

    
