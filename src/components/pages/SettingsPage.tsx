"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Settings,
  Key,
  Eye,
  EyeOff,
  Check,
  X,
  Server,
  FolderOpen,
} from "lucide-react";
import { fetchHealth } from "@/lib/api";

interface EnvVar {
  key: string;
  value: string;
  desc: string;
}

export default function SettingsPage() {
  const [health, setHealth] = useState<{
    status: string;
    hermes_repo: string;
    hermes_repo_exists: boolean;
    evolution_dir: string;
    evolution_dir_exists: boolean;
    skills_count: number;
  } | null>(null);

  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => {});
  }, []);

  const envVars: EnvVar[] = [
    { key: "OPENAI_API_KEY", value: "sk-...", desc: "Used by DSPy for LLM calls" },
    { key: "OPENAI_BASE_URL", value: "http://localhost:11434/v1", desc: "Ollama endpoint" },
    { key: "HERMES_AGENT_REPO", value: health?.hermes_repo || "~/.hermes/hermes-agent", desc: "Path to hermes-agent repo" },
  ];

  return (
    <div className="space-y-6 max-w-3xl">
      {/* System Paths */}
      <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="glass-card rounded-2xl p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2 mb-4"><Server className="w-4 h-4 text-accent-cyan" />System Paths</h2>
        {health && (
          <div className="space-y-3">
            {[
              { label: "Hermes Agent Repo", path: health.hermes_repo, exists: health.hermes_repo_exists },
              { label: "Evolution Engine", path: health.evolution_dir, exists: health.evolution_dir_exists },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center gap-3"><FolderOpen className="w-4 h-4 text-muted-foreground" /><div><p className="text-sm font-medium">{item.label}</p><p className="text-[10px] font-mono text-muted-foreground">{item.path}</p></div></div>
                {item.exists ? <Check className="w-4 h-4 text-success" /> : <X className="w-4 h-4 text-error" />}
              </div>
            ))}
            <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
              <div className="flex items-center gap-3"><FolderOpen className="w-4 h-4 text-muted-foreground" /><div><p className="text-sm font-medium">Skills Found</p></div></div>
              <span className="text-sm font-mono text-accent-violet">{health.skills_count}</span>
            </div>
          </div>
        )}
      </motion.div>

      {/* Environment Variables */}
      <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card rounded-2xl p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2 mb-4"><Key className="w-4 h-4 text-accent-violet" />Environment Variables</h2>
        <div className="space-y-3">
          {envVars.map((env) => (
            <div key={env.key} className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono text-accent-cyan">{env.key}</span>
                <button onClick={() => setShowKeys((prev) => ({ ...prev, [env.key]: !prev[env.key] }))} className="text-muted-foreground/50 hover:text-muted-foreground">{showKeys[env.key] ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}</button>
              </div>
              <p className="text-xs font-mono text-muted-foreground">{showKeys[env.key] ? env.value : "••••••••••••"}</p>
              <p className="text-[10px] text-muted-foreground/50 mt-1">{env.desc}</p>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-muted-foreground/40 mt-4">Set these in your shell or .env file. The backend reads them on startup.</p>
      </motion.div>
    </div>
  );
}
