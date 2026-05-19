"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Terminal, Package, Download, CheckCircle2 } from "lucide-react";

interface LogLine {
  text: string;
  type: "info" | "success" | "warning" | "command";
}

const installLogs: LogLine[] = [
  { text: "$ pip install -r requirements.txt", type: "command" },
  { text: "Collecting dspy>=3.0.0...", type: "info" },
  { text: "  Downloading dspy-3.0.2-py3-none-any.whl (892 kB)", type: "info" },
  { text: "Collecting openai>=1.0.0...", type: "info" },
  { text: "  Downloading openai-1.76.0-py3-none-any.whl (455 kB)", type: "info" },
  { text: "Collecting pyyaml>=6.0...", type: "info" },
  { text: "  Downloading PyYAML-6.0.2-cp312-cp312-linux_x86_64.whl (752 kB)", type: "info" },
  { text: "Installing collected packages: dspy, openai, pyyaml, click, rich", type: "info" },
  { text: "Successfully installed dspy-3.0.2 openai-1.76.0", type: "success" },
  { text: "✓ All dependencies resolved", type: "success" },
];

const deps = [
  { name: "dspy", version: "3.0.2", done: true },
  { name: "openai", version: "1.76.0", done: true },
  { name: "pyyaml", version: "6.0.2", done: true },
  { name: "click", version: "8.1.8", done: true },
  { name: "rich", version: "13.9.4", done: true },
];

export default function EnvironmentStatus() {
  const [visibleLines, setVisibleLines] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisibleLines((prev) => {
        if (prev >= installLogs.length) {
          clearInterval(interval);
          return prev;
        }
        return prev + 1;
      });
    }, 400);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    setProgress((visibleLines / installLogs.length) * 100);
  }, [visibleLines]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.7, duration: 0.6 }}
      className="glass-card rounded-2xl p-6 md:p-8"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 rounded-lg bg-white/[0.05] flex items-center justify-center">
          <Terminal className="w-4 h-4 text-muted-foreground" />
        </div>
        <div>
          <h2 className="text-sm font-semibold tracking-wide uppercase">
            Environment Status
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Dependency installation
          </p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted-foreground flex items-center gap-2">
            <Download className="w-3 h-3" />
            Installing dependencies
          </span>
          <span className="text-xs font-mono text-accent-violet">
            {Math.round(progress)}%
          </span>
        </div>
        <div className="h-1 bg-white/[0.05] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="h-full rounded-full progress-glow"
            style={{
              background: "linear-gradient(90deg, #8b5cf6, #06b6d4)",
            }}
          />
        </div>
      </div>

      {/* Terminal */}
      <div className="rounded-xl bg-black/50 border border-white/[0.04] overflow-hidden">
        {/* Terminal header */}
        <div className="flex items-center gap-2 px-4 py-2 border-b border-white/[0.04] bg-white/[0.02]">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-error/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-warning/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-success/60" />
          </div>
          <span className="text-[10px] text-muted-foreground/50 ml-2 font-mono">
            hermes-env — bash
          </span>
        </div>

        {/* Terminal body */}
        <div className="p-4 font-mono text-xs leading-relaxed h-48 overflow-y-auto">
          {installLogs.slice(0, visibleLines).map((line, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className={`${
                line.type === "command"
                  ? "text-accent-cyan"
                  : line.type === "success"
                  ? "text-success"
                  : line.type === "warning"
                  ? "text-warning"
                  : "text-muted-foreground/70"
              }`}
            >
              {line.text}
            </motion.div>
          ))}
          {visibleLines < installLogs.length && (
            <span className="cursor-blink text-muted-foreground/30" />
          )}
        </div>
      </div>

      {/* Dependencies list */}
      <div className="mt-4 space-y-2">
        {deps.map((dep, i) => (
          <motion.div
            key={dep.name}
            initial={{ opacity: 0 }}
            animate={{ opacity: visibleLines > i + 3 ? 1 : 0.3 }}
            className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-white/[0.01]"
          >
            <div className="flex items-center gap-2">
              <Package className="w-3 h-3 text-muted-foreground/50" />
              <span className="text-xs font-mono text-muted-foreground">
                {dep.name}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-muted-foreground/40">
                {dep.version}
              </span>
              {visibleLines > i + 3 && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 500 }}
                >
                  <CheckCircle2 className="w-3 h-3 text-success" />
                </motion.div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
