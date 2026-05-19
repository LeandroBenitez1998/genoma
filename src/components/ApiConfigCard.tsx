"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Key, Check, X, Loader2, Eye, EyeOff, Globe, Cpu } from "lucide-react";

interface ApiField {
  key: string;
  label: string;
  placeholder: string;
  icon: React.ReactNode;
  status: "idle" | "testing" | "success" | "error";
}

export default function ApiConfigCard() {
  const [fields, setFields] = useState<ApiField[]>([
    {
      key: "OPENAI_API_KEY",
      label: "OpenAI API Key",
      placeholder: "sk-...",
      icon: <Globe className="w-4 h-4" />,
      status: "idle",
    },
    {
      key: "NOUS_API_KEY",
      label: "Nous API Key",
      placeholder: "nous-...",
      icon: <Cpu className="w-4 h-4" />,
      status: "idle",
    },
    {
      key: "OLLAMA_ENDPOINT",
      label: "Ollama Endpoint",
      placeholder: "http://localhost:11434",
      icon: <Key className="w-4 h-4" />,
      status: "idle",
    },
  ]);

  const [values, setValues] = useState<Record<string, string>>({});
  const [showValues, setShowValues] = useState<Record<string, boolean>>({});

  const testConnection = async (fieldKey: string) => {
    setFields((prev) =>
      prev.map((f) => (f.key === fieldKey ? { ...f, status: "testing" } : f))
    );

    // Simulate API test
    await new Promise((resolve) => setTimeout(resolve, 1500));

    const success = values[fieldKey]?.length > 0;
    setFields((prev) =>
      prev.map((f) =>
        f.key === fieldKey
          ? { ...f, status: success ? "success" : "error" }
          : f
      )
    );

    // Reset after 3s
    setTimeout(() => {
      setFields((prev) =>
        prev.map((f) =>
          f.key === fieldKey ? { ...f, status: "idle" } : f
        )
      );
    }, 3000);
  };

  const statusColor = (status: ApiField["status"]) => {
    switch (status) {
      case "testing":
        return "text-accent-cyan";
      case "success":
        return "text-success";
      case "error":
        return "text-error";
      default:
        return "text-muted-foreground";
    }
  };

  const statusIcon = (status: ApiField["status"]) => {
    switch (status) {
      case "testing":
        return <Loader2 className="w-4 h-4 animate-spin" />;
      case "success":
        return <Check className="w-4 h-4" />;
      case "error":
        return <X className="w-4 h-4" />;
      default:
        return null;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3, duration: 0.6 }}
      className="glass-card rounded-2xl p-6 md:p-8"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 rounded-lg bg-accent-violet/10 flex items-center justify-center">
          <Key className="w-4 h-4 text-accent-violet" />
        </div>
        <div>
          <h2 className="text-sm font-semibold tracking-wide uppercase">
            API Configuration
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Configure your model endpoints
          </p>
        </div>
      </div>

      {/* Fields */}
      <div className="space-y-4">
        {fields.map((field, index) => (
          <motion.div
            key={field.key}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 + index * 0.1 }}
            className="space-y-2"
          >
            <label className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              {field.icon}
              {field.label}
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type={showValues[field.key] ? "text" : "password"}
                  placeholder={field.placeholder}
                  value={values[field.key] || ""}
                  onChange={(e) =>
                    setValues((prev) => ({ ...prev, [field.key]: e.target.value }))
                  }
                  className="w-full px-4 py-2.5 rounded-xl bg-white/[0.02] border border-white/[0.06] text-sm text-foreground placeholder:text-muted-foreground/50 transition-all duration-200"
                />
                <button
                  onClick={() =>
                    setShowValues((prev) => ({
                      ...prev,
                      [field.key]: !prev[field.key],
                    }))
                  }
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-muted-foreground transition-colors"
                >
                  {showValues[field.key] ? (
                    <EyeOff className="w-3.5 h-3.5" />
                  ) : (
                    <Eye className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => testConnection(field.key)}
                disabled={field.status === "testing"}
                className={`px-4 py-2.5 rounded-xl text-xs font-medium border transition-all duration-300 flex items-center gap-2 min-w-[120px] justify-center ${
                  field.status === "success"
                    ? "bg-success/10 border-success/30 text-success"
                    : field.status === "error"
                    ? "bg-error/10 border-error/30 text-error"
                    : field.status === "testing"
                    ? "bg-accent-cyan/10 border-accent-cyan/30 text-accent-cyan"
                    : "bg-white/[0.02] border-white/[0.06] text-muted-foreground hover:border-white/10 hover:text-foreground"
                }`}
              >
                <AnimatePresence mode="wait">
                  <motion.span
                    key={field.status}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -5 }}
                    className="flex items-center gap-2"
                  >
                    {statusIcon(field.status)}
                    {field.status === "idle"
                      ? "Test"
                      : field.status === "testing"
                      ? "Testing..."
                      : field.status === "success"
                      ? "Connected"
                      : "Failed"}
                  </motion.span>
                </AnimatePresence>
              </motion.button>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
