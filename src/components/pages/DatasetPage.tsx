"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Database,
  FileJson,
  Loader2,
  BarChart3,
  Sparkles,
  RefreshCw,
  FolderOpen,
} from "lucide-react";
import { fetchDatasets, fetchDataset, type DatasetInfo, api } from "@/lib/api";

export default function DatasetPage() {
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [examples, setExamples] = useState<Record<string, unknown[]> | null>(null);
  const [activeSplit, setActiveSplit] = useState("train");
  const [loading, setLoading] = useState(true);
  const [examplesLoading, setExamplesLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [genMsg, setGenMsg] = useState("");

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = () => {
    setLoading(true);
    fetchDatasets()
      .then(setDatasets)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const selectDataset = async (skill: string) => {
    setSelected(skill);
    setExamplesLoading(true);
    setActiveSplit("train");
    try {
      const data = await fetchDataset(skill);
      setExamples(data);
    } catch {
      setExamples(null);
    }
    setExamplesLoading(false);
  };

  const handleGenerate = async (skill: string) => {
    setGenerating(true);
    setGenMsg("Generando...");
    try {
      // Generate 10 examples for this skill
      const res = await fetch(`/api/datasets/generate?skill_name=${skill}&count=10`, {
        method: "POST",
      });
      const data = await res.json();
      if (data.status === "ok") {
        setGenMsg(`✅ ${data.stdout?.split("\n").pop() || "Done!"}`);
        loadDatasets(); // refresh
        if (selected === skill) selectDataset(skill); // reload examples
      } else {
        setGenMsg(`❌ ${data.stderr || "Error"}`);
      }
    } catch (e) {
      setGenMsg(`❌ ${e instanceof Error ? e.message : "Failed"}`);
    }
    setGenerating(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[var(--evo-primary-100)] flex items-center justify-center">
            <Database className="w-5 h-5 text-[var(--evo-primary-700)]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Datasets</h1>
            <p className="text-[var(--evo-text-secondary)] text-sm">
              Holdout + training data para validación real de skills
            </p>
          </div>
        </div>
        <button
          onClick={loadDatasets}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--evo-bg-surface)] border rounded-xl transition-all"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Dataset grid */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      ) : datasets.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center">
          <FileJson className="w-10 h-10 text-muted-foreground/30 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No datasets yet</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Generate training data or add holdout examples manually
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {datasets.map((ds) => (
            <motion.div
              key={ds.skill}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`glass-card rounded-2xl p-5 cursor-pointer transition-all border ${
                selected === ds.skill
                  ? "border-accent-violet/40 shadow-accent-violet/5"
                  : "border-white/[0.06] hover:border-white/[0.12]"
              }`}
              onClick={() => selectDataset(ds.skill)}
            >
              <div className="flex items-center gap-2 mb-3">
                <FolderOpen className="w-4 h-4 text-accent-violet" />
                <h3 className="font-semibold text-sm">{ds.skill}</h3>
              </div>

              {/* Split badges */}
              <div className="flex gap-2 mb-3">
                {Object.entries(ds.splits).map(([name, count]) => (
                  <span
                    key={name}
                    className={`text-[10px] px-2 py-0.5 rounded font-mono ${
                      name === "holdout"
                        ? "bg-error/10 text-error"
                        : name === "val"
                        ? "bg-accent-cyan/10 text-accent-cyan"
                        : "bg-white/[0.05] text-muted-foreground"
                    }`}
                  >
                    {name}: {count}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  {ds.total} total examples
                </span>
                <BarChart3 className="w-3.5 h-3.5 text-muted-foreground/50" />
              </div>

              {/* Generate button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleGenerate(ds.skill);
                }}
                disabled={generating}
                className="w-full mt-3 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium bg-accent-violet/10 text-accent-violet hover:bg-accent-violet/20 transition-colors disabled:opacity-50"
              >
                {generating ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Sparkles className="w-3 h-3" />
                )}
                Generate More
              </button>
            </motion.div>
          ))}
        </div>
      )}

      {/* Example viewer */}
      {selected && (
        <div className="glass-card rounded-2xl overflow-hidden">
          <div className="px-4 py-3 border-b border-white/[0.06] flex items-center justify-between">
            <div className="flex gap-1">
              {["train", "val", "holdout"].map((split) => {
                const count =
                  (examples?.[split] as Array<unknown>)?.length ?? 0;
                return (
                  <button
                    key={split}
                    onClick={() => setActiveSplit(split)}
                    disabled={count === 0}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      activeSplit === split
                        ? "bg-accent-violet/15 text-accent-violet"
                        : count === 0
                        ? "text-muted-foreground/30"
                        : "text-muted-foreground hover:text-foreground hover:bg-white/[0.03]"
                    }`}
                  >
                    {split} ({count})
                  </button>
                );
              })}
            </div>
            <span className="text-[10px] text-muted-foreground">
              {selected}
            </span>
          </div>

          <div className="p-4 max-h-[60vh] overflow-y-auto space-y-3">
            {examplesLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
              </div>
            ) : (
              (examples?.[activeSplit] as Array<Record<string, string>>)?.map(
                (ex, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]"
                  >
                    <span className="text-[10px] font-mono text-accent-violet mb-2 block">
                      #{i + 1}
                    </span>

                    {/* Input field — handles both "input" and "task_input" */}
                    {(ex.input || ex.task_input) && (
                      <div className="mb-2">
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
                          Input
                        </span>
                        <pre className="text-xs text-foreground mt-1 whitespace-pre-wrap font-mono bg-black/20 rounded-lg p-2 max-h-32 overflow-y-auto">
                          {(ex.input || ex.task_input || "").slice(0, 500)}
                        </pre>
                      </div>
                    )}

                    {/* Expected field */}
                    {(ex.expected || ex.expected_behavior) && (
                      <div>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
                          Expected
                        </span>
                        <p className="text-xs text-muted-foreground mt-1">
                          {(ex.expected || ex.expected_behavior || "").slice(
                            0,
                            400
                          )}
                        </p>
                      </div>
                    )}
                  </motion.div>
                )
              )
            )}
          </div>
        </div>
      )}

      {genMsg && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-xs text-muted-foreground text-center"
        >
          {genMsg}
        </motion.div>
      )}
    </div>
  );
}
