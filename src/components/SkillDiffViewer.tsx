"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  GitBranch,
  Loader2,
  FileText,
  Code2,
  X,
} from "lucide-react";
import { fetchSkillDiff, type SkillDiff } from "@/lib/api";

interface SkillDiffViewerProps {
  skillName: string;
  runDir: string;
  onClose: () => void;
}

export default function SkillDiffViewer({
  skillName,
  runDir,
  onClose,
}: SkillDiffViewerProps) {
  const [diff, setDiff] = useState<SkillDiff | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"baseline" | "evolved" | "diff">("baseline");

  useEffect(() => {
    setLoading(true);
    fetchSkillDiff(skillName, runDir)
      .then(setDiff)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [skillName, runDir]);

  if (loading) {
    return (
      <div className="mt-3 p-4 rounded-xl bg-black/30 border border-white/[0.06] flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" />
        Loading diff...
      </div>
    );
  }

  if (error || !diff) {
    return (
      <div className="mt-3 p-4 rounded-xl bg-error/5 border border-error/10 text-sm text-error">
        Failed to load diff: {error || "Unknown error"}
      </div>
    );
  }

  const computeDiff = () => {
    if (!diff.baseline || !diff.evolved) return null;
    const baseLines = diff.baseline.split("\n");
    const evoLines = diff.evolved.split("\n");
    const result: { type: "same" | "add" | "remove"; line: string; baseNum: number; evoNum: number }[] = [];
    let bi = 0, ei = 0;
    while (bi < baseLines.length || ei < evoLines.length) {
      if (bi >= baseLines.length) {
        result.push({ type: "add", line: evoLines[ei], baseNum: bi + 1, evoNum: ei + 1 });
        ei++;
      } else if (ei >= evoLines.length) {
        result.push({ type: "remove", line: baseLines[bi], baseNum: bi + 1, evoNum: ei + 1 });
        bi++;
      } else if (baseLines[bi] === evoLines[ei]) {
        result.push({ type: "same", line: baseLines[bi], baseNum: bi + 1, evoNum: ei + 1 });
        bi++; ei++;
      } else {
        result.push({ type: "remove", line: baseLines[bi], baseNum: bi + 1, evoNum: ei + 1 });
        result.push({ type: "add", line: evoLines[ei], baseNum: bi + 1, evoNum: ei + 1 });
        bi++; ei++;
      }
    }
    return result;
  };

  const diffLines = computeDiff();

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      className="mt-3 overflow-hidden"
    >
      <div className="rounded-xl bg-black/40 border border-white/[0.06] overflow-hidden">
        <div className="flex items-center justify-between px-3 py-2 border-b border-white/[0.06]">
          <div className="flex items-center gap-1">
            <button
              onClick={() => setActiveTab("baseline")}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                activeTab === "baseline" ? "bg-white/[0.08] text-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="w-3 h-3 inline mr-1" />
              Before
            </button>
            <button
              onClick={() => setActiveTab("evolved")}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                activeTab === "evolved" ? "bg-white/[0.08] text-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Code2 className="w-3 h-3 inline mr-1" />
              After
            </button>
            {diffLines && (
              <button
                onClick={() => setActiveTab("diff")}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                  activeTab === "diff" ? "bg-white/[0.08] text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <GitBranch className="w-3 h-3 inline mr-1" />
                Diff
              </button>
            )}
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/[0.05] transition-colors">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="max-h-96 overflow-y-auto">
          {activeTab === "baseline" && diff.baseline && (
            <pre className="p-4 text-xs font-mono leading-relaxed text-muted-foreground whitespace-pre-wrap">{diff.baseline}</pre>
          )}
          {activeTab === "evolved" && diff.evolved && (
            <pre className="p-4 text-xs font-mono leading-relaxed text-muted-foreground whitespace-pre-wrap">{diff.evolved}</pre>
          )}
          {activeTab === "diff" && diffLines && (
            <div className="p-4 text-xs font-mono leading-relaxed">
              {diffLines.map((d, i) => (
                <div
                  key={i}
                  className={`flex gap-2 px-1 -mx-1 rounded ${
                    d.type === "add" ? "bg-success/10 text-success" : d.type === "remove" ? "bg-error/10 text-error" : ""
                  }`}
                >
                  <span className="text-muted-foreground/40 w-8 text-right select-none flex-shrink-0">{d.type === "add" ? d.evoNum : d.baseNum}</span>
                  <span className="text-muted-foreground/40 w-4 select-none flex-shrink-0">{d.type === "add" ? "+" : d.type === "remove" ? "-" : " "}</span>
                  <span className="break-all">{d.line}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
