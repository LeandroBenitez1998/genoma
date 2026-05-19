"use client";

import { useEffect, useState } from "react";

export default function ThemeAwareBackground() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const html = document.documentElement;
    const check = () => setIsDark(html.classList.contains("dark"));
    check();
    const observer = new MutationObserver(check);
    observer.observe(html, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  return (
    <div className="fixed inset-0 -z-10 pointer-events-none overflow-hidden">
      {/* Light mode gradient */}
      <div
        className={`absolute inset-0 transition-opacity duration-500 ${
          isDark ? "opacity-0" : "opacity-40"
        }`}
        style={{
          background: `
            radial-gradient(ellipse 80% 60% at 0% 20%, rgba(178, 255, 255, 0.6) 0%, transparent 60%),
            radial-gradient(ellipse 60% 50% at 100% 40%, rgba(103, 232, 249, 0.4) 0%, transparent 50%),
            radial-gradient(ellipse 50% 40% at 50% 80%, rgba(236, 254, 255, 0.3) 0%, transparent 50%),
            transparent
          `,
          animation: "ambient-drift 12s ease-in-out infinite alternate",
        }}
      />
      {/* Dark mode gradient */}
      <div
        className={`absolute inset-0 transition-opacity duration-500 ${
          isDark ? "opacity-30" : "opacity-0"
        }`}
        style={{
          background: `
            radial-gradient(ellipse 70% 50% at 20% 30%, rgba(6, 182, 212, 0.15) 0%, transparent 60%),
            radial-gradient(ellipse 50% 40% at 80% 60%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
            transparent
          `,
          animation: "ambient-drift 15s ease-in-out infinite alternate-reverse",
        }}
      />
      {/* Noise overlay */}
      <div
        className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E\")",
          backgroundSize: "256px 256px",
        }}
      />
      <style jsx>{`
        @keyframes ambient-drift {
          0% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(2%, -1%) scale(1.02); }
          66% { transform: translate(-1%, 2%) scale(0.98); }
          100% { transform: translate(1%, 1%) scale(1.01); }
        }
      `}</style>
    </div>
  );
}
