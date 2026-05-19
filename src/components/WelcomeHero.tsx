"use client";

import { motion } from "framer-motion";
import { Sparkles, Dna } from "lucide-react";

export default function WelcomeHero() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="relative flex flex-col items-center justify-center py-20 px-4 overflow-hidden"
    >
      {/* Background orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.08, 0.15, 0.08] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full"
          style={{
            background: "radial-gradient(circle, rgba(139,92,246,0.3) 0%, transparent 70%)",
          }}
        />
        <motion.div
          animate={{ scale: [1.2, 1, 1.2], opacity: [0.08, 0.12, 0.08] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full"
          style={{
            background: "radial-gradient(circle, rgba(6,182,212,0.3) 0%, transparent 70%)",
          }}
        />
      </div>

      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.3, duration: 0.5 }}
        className="flex items-center gap-2 px-4 py-1.5 rounded-full glass-card mb-6"
      >
        <Dna className="w-3.5 h-3.5 text-accent-violet" />
        <span className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
          Autonomous Evolution Interface
        </span>
        <Sparkles className="w-3.5 h-3.5 text-accent-cyan" />
      </motion.div>

      {/* Title */}
      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.8 }}
        className="text-5xl md:text-7xl font-bold text-center leading-tight tracking-tight"
      >
        <span className="gradient-text">Genoma</span>
      </motion.h1>

      {/* Subtitle */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8, duration: 0.6 }}
        className="mt-4 text-lg md:text-xl text-muted-foreground text-center max-w-xl"
      >
        Self-evolving intelligence. Zero-friction setup.
      </motion.p>

      {/* Divider line */}
      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ delay: 1.0, duration: 0.8, ease: "easeOut" }}
        className="mt-10 w-full max-w-2xl h-px bg-gradient-to-r from-transparent via-white/10 to-transparent"
      />
    </motion.section>
  );
}
