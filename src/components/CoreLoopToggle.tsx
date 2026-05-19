"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Power, Activity } from "lucide-react";

export default function CoreLoopToggle() {
  const [active, setActive] = useState(false);
  const [statusText, setStatusText] = useState("Standby");

  const handleToggle = () => {
    const next = !active;
    setActive(next);
    setStatusText(next ? "Running" : "Standby");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5, duration: 0.6 }}
      className="glass-card rounded-2xl p-6 md:p-8"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 rounded-lg bg-accent-cyan/10 flex items-center justify-center">
          <Activity className="w-4 h-4 text-accent-cyan" />
        </div>
        <div>
          <h2 className="text-sm font-semibold tracking-wide uppercase">
            Core Evolution Loop
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            hermes_core_loop.py
          </p>
        </div>
      </div>

      {/* Toggle + Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* LED indicator */}
          <div className="relative">
            <div
              className={`w-2.5 h-2.5 rounded-full ${
                active ? "bg-success" : "bg-muted"
              } ${active ? "led-pulse" : ""}`}
              style={{ color: "#22c55e" }}
            />
            {active && (
              <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-success animate-ping opacity-20" />
            )}
          </div>
          <span className="text-sm text-muted-foreground">
            {statusText}
          </span>
        </div>

        {/* iOS-style toggle */}
        <button
          onClick={handleToggle}
          className="relative focus:outline-none"
          aria-label="Toggle core loop"
        >
          <motion.div
            className={`w-14 h-8 rounded-full p-1 transition-colors duration-300 ${
              active
                ? "bg-accent-violet"
                : "bg-white/10"
            }`}
          >
            <motion.div
              animate={{ x: active ? 24 : 0 }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
              className="w-6 h-6 rounded-full bg-white shadow-lg flex items-center justify-center"
            >
              <Power
                className={`w-3 h-3 transition-colors ${
                  active ? "text-accent-violet" : "text-muted-foreground"
                }`}
              />
            </motion.div>
          </motion.div>
        </button>
      </div>

      {/* Status bar when active */}
      {active && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-4 pt-4 border-t border-white/[0.06]"
        >
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Evolution cycle</span>
            <span className="text-accent-cyan font-mono">#1</span>
          </div>
          <div className="flex items-center justify-between text-xs mt-2">
            <span className="text-muted-foreground">Population</span>
            <span className="text-accent-violet font-mono">5 / 5</span>
          </div>
          <div className="flex items-center justify-between text-xs mt-2">
            <span className="text-muted-foreground">Best fitness</span>
            <span className="text-success font-mono">0.87</span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
