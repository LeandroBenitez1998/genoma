"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Terminal, Wifi, WifiOff, Trash2, ChevronDown, Activity, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { wsConnect, fetchJobs, fetchJobLogs, type EvolutionJob } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  completed: "text-success",
  failed: "text-error",
  running: "text-accent-violet",
};

export default function LogsPage() {
  const [wsLogs, setWsLogs] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);
  const [jobs, setJobs] = useState<EvolutionJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [jobLogs, setJobLogs] = useState<string[]>([]);
  const [jobStatus, setJobStatus] = useState("");
  const terminalRef = useRef<HTMLDivElement>(null);
  const logIndex = useRef(0);

  // Load all jobs on mount
  useEffect(() => {
    fetchJobs(false).then(setJobs).catch(() => {});
  }, []);

  // WebSocket for live stream
  useEffect(() => {
    let ws: WebSocket | null = null;
    let cancelled = false;

    wsConnect((data) => {
      if (cancelled) return;
      const entry = data as { type: string; message?: string; timestamp?: string; job_id?: string; skill?: string };
      if (entry.type === "evolution_log" && entry.message) {
        const ts = entry.timestamp?.slice(11, 19) || "";
        const skill = entry.skill ? `[${entry.skill}] ` : "";
        setWsLogs((prev) => [...prev.slice(-1000), `${ts} ${skill}${entry.message}`]);

        // Refresh jobs list when new activity
        fetchJobs(false).then(setJobs).catch(() => {});
      }
      if (entry.type === "evolution_complete" || entry.type === "evolution_cancelled") {
        fetchJobs(false).then(setJobs).catch(() => {});
      }
    }).then((sock) => {
      if (cancelled) { sock.close(); return; }
      ws = sock;
      sock.onopen = () => setConnected(true);
      sock.onclose = () => setConnected(false);
      sock.onerror = () => setConnected(false);
    });

    return () => { cancelled = true; ws?.close(); };
  }, []);

  // Load logs for selected job
  useEffect(() => {
    if (!selectedJob) {
      setJobLogs([]);
      setJobStatus("");
      return;
    }

    const job = jobs.find((j) => j.id === selectedJob);
    if (!job) return;

    // Load initial logs
    setJobLogs(job.logs || []);
    logIndex.current = (job.logs || []).length;
    setJobStatus(job.status);

    // Poll for new logs if job is active
    const isActive = job.status !== "completed" && job.status !== "failed";
    if (!isActive) return;

    const interval = setInterval(async () => {
      try {
        const data = await fetchJobLogs(selectedJob, logIndex.current);
        if (data.logs?.length) {
          setJobLogs((prev) => [...prev, ...data.logs]);
          logIndex.current = data.total_lines;
        }
        setJobStatus(data.status);

        // Refresh jobs list
        if (data.status === "completed" || data.status === "failed") {
          fetchJobs(false).then(setJobs).catch(() => {});
        }
      } catch {}
    }, 1500);

    return () => clearInterval(interval);
  }, [selectedJob, jobs]);

  // Auto-scroll
  useEffect(() => {
    if (terminalRef.current) terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
  }, [wsLogs, jobLogs]);

  const activeJobs = jobs.filter((j) => j.status !== "completed" && j.status !== "failed");
  const completedJobs = jobs.filter((j) => j.status === "completed" || j.status === "failed");

  const formatTime = (iso: string) => {
    if (!iso) return "";
    return iso.slice(11, 19);
  };

  return (
    <div className="flex gap-6 h-[calc(100vh-4rem)]">
      {/* Job sidebar */}
      <div className="w-72 flex-shrink-0 glass-card rounded-2xl flex flex-col overflow-hidden">
        <div className="px-4 py-4 border-b border-white/[0.06]">
          <h2 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-accent-violet" />
            Evolution Jobs
          </h2>
          <p className="text-[10px] text-muted-foreground mt-1">{jobs.length} total · {activeJobs.length} active</p>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {/* Live stream option */}
          <button
            onClick={() => setSelectedJob(null)}
            className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all ${
              selectedJob === null ? "bg-white/[0.06] text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-white/[0.03]"
            }`}
          >
            <div className="flex items-center gap-2">
              <Wifi className={`w-3 h-3 ${connected ? "text-success" : "text-error"}`} />
              <span className="font-medium">Live Stream</span>
            </div>
            <p className="text-[10px] text-muted-foreground mt-0.5">WebSocket real-time</p>
          </button>

          {/* Active jobs */}
          {activeJobs.length > 0 && (
            <>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider px-3 pt-2">Active</p>
              {activeJobs.map((job) => (
                <button
                  key={job.id}
                  onClick={() => setSelectedJob(job.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all ${
                    selectedJob === job.id ? "bg-white/[0.06] text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-white/[0.03]"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-3 h-3 text-accent-violet animate-spin" />
                    <span className="truncate">{job.skill_name}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] font-mono text-accent-violet">{job.status}</span>
                    {job.status === "optimizing" && (
                      <span className="text-[10px] font-mono text-muted-foreground">
                        {job.current_iteration}/{job.iterations}
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </>
          )}

          {/* Completed jobs */}
          {completedJobs.length > 0 && (
            <>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider px-3 pt-2">Completed</p>
              {completedJobs.map((job) => (
                <button
                  key={job.id}
                  onClick={() => setSelectedJob(job.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all ${
                    selectedJob === job.id ? "bg-white/[0.06] text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-white/[0.03]"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {job.status === "completed" ? (
                      <CheckCircle2 className="w-3 h-3 text-success" />
                    ) : (
                      <XCircle className="w-3 h-3 text-error" />
                    )}
                    <span className="truncate">{job.skill_name}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] font-mono text-muted-foreground">{formatTime(job.completed_at || job.started_at)}</span>
                    {job.improvement !== null && job.improvement !== 0 && (
                      <span className={`text-[10px] font-mono ${job.improvement > 0 ? "text-success" : "text-error"}`}>
                        {job.improvement > 0 ? "+" : ""}{(job.improvement * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </>
          )}

          {jobs.length === 0 && (
            <p className="text-xs text-muted-foreground p-4 text-center">No jobs yet. Start an evolution.</p>
          )}
        </div>
      </div>

      {/* Terminal */}
      <div className="flex-1 glass-card rounded-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <Terminal className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-semibold">
              {selectedJob ? jobs.find((j) => j.id === selectedJob)?.skill_name || "Job" : "Live Stream"}
            </span>
            {selectedJob && jobStatus && (
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                jobStatus === "completed" ? "bg-success/10 text-success" :
                jobStatus === "failed" ? "bg-error/10 text-error" :
                "bg-accent-violet/10 text-accent-violet"
              }`}>
                {jobStatus}
              </span>
            )}
            {!selectedJob && (
              <div className="flex items-center gap-1.5">
                {connected ? <Wifi className="w-3 h-3 text-success" /> : <WifiOff className="w-3 h-3 text-error" />}
                <span className="text-[10px] text-muted-foreground">{connected ? "Connected" : "Disconnected"}</span>
              </div>
            )}
          </div>
          <button
            onClick={() => selectedJob ? setJobLogs([]) : setWsLogs([])}
            className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs text-muted-foreground hover:text-foreground hover:bg-white/[0.05] transition-colors"
          >
            <Trash2 className="w-3 h-3" />
            Clear
          </button>
        </div>

        {/* Log output */}
        <div ref={terminalRef} className="flex-1 overflow-y-auto p-4 font-mono text-xs leading-relaxed bg-black/30">
          {(selectedJob ? jobLogs : wsLogs).length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground/40">
              <Terminal className="w-8 h-8 mb-3" />
              <p>{selectedJob ? "No logs for this job" : "Waiting for events..."}</p>
              <p className="text-[10px] mt-1">{selectedJob ? "The job may not have produced output yet" : "Start an evolution to see live output"}</p>
            </div>
          ) : (
            (selectedJob ? jobLogs : wsLogs).map((line, i) => {
              const isError = /✗|Error|error|FAILED|failed/.test(line);
              const isSuccess = /✓|completed|Saved/.test(line);
              const isPhase = /Loaded:|Building|Validating|Configuring|Running|Evaluating|Optimization|GEPA/.test(line);
              return (
                <div key={i} className={
                  isError ? "text-error" :
                  isSuccess ? "text-success" :
                  isPhase ? "text-accent-cyan font-semibold" :
                  "text-muted-foreground/70"
                }>
                  {line}
                </div>
              );
            })
          )}
          {(!selectedJob || (jobStatus !== "completed" && jobStatus !== "failed")) && (
            <span className="cursor-blink text-muted-foreground/30" />
          )}
        </div>
      </div>
    </div>
  );
}
