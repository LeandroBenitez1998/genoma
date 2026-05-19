"use client";

export default function GlitchText({
  children,
  speed = 1,
  enableShadows = true,
  className = "",
}: {
  children: string;
  speed?: number;
  enableShadows?: boolean;
  className?: string;
}) {
  return (
    <div
      className={`relative inline-block font-bold ${className}`}
      data-text={children}
      style={{
        animation: `glitch-anim ${speed * 3}s infinite linear alternate-reverse`,
      }}
    >
      <style>{`
        @keyframes glitch-anim {
          0% { text-shadow: ${enableShadows ? "-2px 0 red, 2px 0 cyan" : "none"}; }
          25% { text-shadow: ${enableShadows ? "2px 0 red, -2px 0 cyan" : "none"}; }
          50% { text-shadow: ${enableShadows ? "-1px 2px red, 1px -2px cyan" : "none"}; }
          75% { text-shadow: ${enableShadows ? "1px -1px red, -1px 1px cyan" : "none"}; }
          100% { text-shadow: ${enableShadows ? "0 0 red, 0 0 cyan" : "none"}; }
        }
      `}</style>
      {children}
    </div>
  );
}
