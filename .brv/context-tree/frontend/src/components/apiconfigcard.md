---
title: ApiConfigCard
summary: Source file components/ApiConfigCard.tsx in the Next.js frontend
tags: []
related: []
keywords: []
createdAt: '2026-05-21T07:39:26.018Z'
updatedAt: '2026-05-21T07:39:26.018Z'
---
## Reason
Curate components/ApiConfigCard.tsx from src folder

## Raw Concept
**Task:**
Document components/ApiConfigCard.tsx

**Timestamp:** 2026-05-21

## Narrative
### Structure
Implementation for components/ApiConfigCard.tsx

### Highlights
Captured complete source content from components/ApiConfigCard.tsx

---


&quot;use client&quot;;

import { useState } from &quot;react&quot;;
import { motion, AnimatePresence } from &quot;framer-motion&quot;;
import { Key, Check, X, Loader2, Eye, EyeOff, Globe, Cpu } from &quot;lucide-react&quot;;

interface ApiField {
  key: string;
  label: string;
  placeholder: string;
  icon: React.ReactNode;
  status: &quot;idle&quot; | &quot;testing&quot; | &quot;success&quot; | &quot;error&quot;;
}

export default function ApiConfigCard() {
  const [fields, setFields] = useState&lt;ApiField[]&gt;([
    {
      key: &quot;OPENAI_API_KEY&quot;,
      label: &quot;OpenAI API Key&quot;,
      placeholder: &quot;sk-...&quot;,
      icon: &lt;Globe className=&quot;w-4 h-4&quot; /&gt;,
      status: &quot;idle&quot;,
    },
    {
      key: &quot;NOUS_API_KEY&quot;,
      label: &quot;Nous API Key&quot;,
      placeholder: &quot;nous-...&quot;,
      icon: &lt;Cpu className=&quot;w-4 h-4&quot; /&gt;,
      status: &quot;idle&quot;,
    },
    {
      key: &quot;OLLAMA_ENDPOINT&quot;,
      label: &quot;Ollama Endpoint&quot;,
      placeholder: &quot;http://localhost:11434&quot;,
      icon: &lt;Key className=&quot;w-4 h-4&quot; /&gt;,
      status: &quot;idle&quot;,
    },
  ]);

  const [values, setValues] = useState&lt;Record&lt;string, string&gt;&gt;({});
  const [showValues, setShowValues] = useState&lt;Record&lt;string, boolean&gt;&gt;({});

  const testConnection = async (fieldKey: string) =&gt; {
    setFields((prev) =&gt;
      prev.map((f) =&gt; (f.key === fieldKey ? { ...f, status: &quot;testing&quot; } : f))
    );

    // Simulate API test
    await new Promise((resolve) =&gt; setTimeout(resolve, 1500));

    const success = values[fieldKey]?.length &gt; 0;
    setFields((prev) =&gt;
      prev.map((f) =&gt;
        f.key === fieldKey
          ? { ...f, status: success ? &quot;success&quot; : &quot;error&quot; }
          : f
      )
    );

    // Reset after 3s
    setTimeout(() =&gt; {
      setFields((prev) =&gt;
        prev.map((f) =&gt;
          f.key === fieldKey ? { ...f, status: &quot;idle&quot; } : f
        )
      );
    }, 3000);
  };

  const statusColor = (status: ApiField[&quot;status&quot;]) =&gt; {
    switch (status) {
      case &quot;testing&quot;:
        return &quot;text-accent-cyan&quot;;
      case &quot;success&quot;:
        return &quot;text-success&quot;;
      case &quot;error&quot;:
        return &quot;text-error&quot;;
      default:
        return &quot;text-muted-foreground&quot;;
    }
  };

  const statusIcon = (status: ApiField[&quot;status&quot;]) =&gt; {
    switch (status) {
      case &quot;testing&quot;:
        return &lt;Loader2 className=&quot;w-4 h-4 animate-spin&quot; /&gt;;
      case &quot;success&quot;:
        return &lt;Check className=&quot;w-4 h-4&quot; /&gt;;
      case &quot;error&quot;:
        return &lt;X className=&quot;w-4 h-4&quot; /&gt;;
      default:
        return null;
    }
  };

  return (
    &lt;motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3, duration: 0.6 }}
      className=&quot;glass-card rounded-2xl p-6 md:p-8&quot;
    &gt;
      {/* Header */}
      &lt;div className=&quot;flex items-center gap-3 mb-6&quot;&gt;
        &lt;div className=&quot;w-8 h-8 rounded-lg bg-accent-violet/10 flex items-center justify-center&quot;&gt;
          &lt;Key className=&quot;w-4 h-4 text-accent-violet&quot; /&gt;
        &lt;/div&gt;
        &lt;div&gt;
          &lt;h2 className=&quot;text-sm font-semibold tracking-wide uppercase&quot;&gt;
            API Configuration
          &lt;/h2&gt;
          &lt;p className=&quot;text-xs text-muted-foreground mt-0.5&quot;&gt;
            Configure your model endpoints
          &lt;/p&gt;
        &lt;/div&gt;
      &lt;/div&gt;

      {/* Fields */}
      &lt;div className=&quot;space-y-4&quot;&gt;
        {fields.map((field, index) =&gt; (
          &lt;motion.div
            key={field.key}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 + index * 0.1 }}
            className=&quot;space-y-2&quot;
          &gt;
            &lt;label className=&quot;flex items-center gap-2 text-xs font-medium text-muted-foreground&quot;&gt;
              {field.icon}
              {field.label}
            &lt;/label&gt;
            &lt;div className=&quot;flex gap-2&quot;&gt;
              &lt;div className=&quot;relative flex-1&quot;&gt;
                &lt;input
                  type={showValues[field.key] ? &quot;text&quot; : &quot;password&quot;}
                  placeholder={field.placeholder}
                  value={values[field.key] || &quot;&quot;}
                  onChange={(e) =&gt;
                    setValues((prev) =&gt; ({ ...prev, [field.key]: e.target.value }))
                  }
                  className=&quot;w-full px-4 py-2.5 rounded-xl bg-white/[0.02] border border-white/[0.06] text-sm text-foreground placeholder:text-muted-foreground/50 transition-all duration-200&quot;
                /&gt;
                &lt;button
                  onClick={() =&gt;
                    setShowValues((prev) =&gt; ({
                      ...prev,
                      [field.key]: !prev[field.key],
                    }))
                  }
                  className=&quot;absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-muted-foreground transition-colors&quot;
                &gt;
                  {showValues[field.key] ? (
                    &lt;EyeOff className=&quot;w-3.5 h-3.5&quot; /&gt;
                  ) : (
                    &lt;Eye className=&quot;w-3.5 h-3.5&quot; /&gt;
                  )}
                &lt;/button&gt;
              &lt;/div&gt;
              &lt;motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() =&gt; testConnection(field.key)}
                disabled={field.status === &quot;testing&quot;}
                className={`px-4 py-2.5 rounded-xl text-xs font-medium border transition-all duration-300 flex items-center gap-2 min-w-[120px] justify-center ${
                  field.status === &quot;success&quot;
                    ? &quot;bg-success/10 border-success/30 text-success&quot;
                    : field.status === &quot;error&quot;
                    ? &quot;bg-error/10 border-error/30 text-error&quot;
                    : field.status === &quot;testing&quot;
                    ? &quot;bg-accent-cyan/10 border-accent-cyan/30 text-accent-cyan&quot;
                    : &quot;bg-white/[0.02] border-white/[0.06] text-muted-foreground hover:border-white/10 hover:text-foreground&quot;
                }`}
              &gt;
                &lt;AnimatePresence mode=&quot;wait&quot;&gt;
                  &lt;motion.span
                    key={field.status}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -5 }}
                    className=&quot;flex items-center gap-2&quot;
                  &gt;
                    {statusIcon(field.status)}
                    {field.status === &quot;idle&quot;
                      ? &quot;Test&quot;
                      : field.status === &quot;testing&quot;
                      ? &quot;Testing...&quot;
                      : field.status === &quot;success&quot;
                      ? &quot;Connected&quot;
                      : &quot;Failed&quot;}
                  &lt;/motion.span&gt;
                &lt;/AnimatePresence&gt;
              &lt;/motion.button&gt;
            &lt;/div&gt;
          &lt;/motion.div&gt;
        ))}
      &lt;/div&gt;
    &lt;/motion.div&gt;
  );
}

    
