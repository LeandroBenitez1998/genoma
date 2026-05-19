"use client";

import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem("genoma-theme");
    const prefersDark = saved ? saved === "dark" : true;
    setIsDark(prefersDark);
    if (prefersDark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const toggle = () => {
    const next = !isDark;
    setIsDark(next);
    localStorage.setItem("genoma-theme", next ? "dark" : "light");
    if (next) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  if (!mounted) {
    return (
      <button className="w-9 h-9 rounded-lg flex items-center justify-center text-gray-400">
        <Sun className="w-5 h-5" />
      </button>
    );
  }

  return (
    <button
      onClick={toggle}
      className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-200 ${
        isDark
          ? "bg-gray-800 text-yellow-400 hover:bg-gray-700"
          : "bg-white text-primary-600 shadow-[var(--evo-shadow-md)] border border-gray-200 hover:bg-[var(--evo-bg-surface-hover)]"
      }`}
      title={isDark ? "Cambiar a Light Mode" : "Cambiar a Dark Mode"}
    >
      {isDark ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
    </button>
  );
}
