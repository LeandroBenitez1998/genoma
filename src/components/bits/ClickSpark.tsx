"use client";

import { useRef, useEffect, useCallback } from "react";

interface ClickSparkProps {
  children: React.ReactNode;
  sparkColor?: string;
  sparkSize?: number;
  sparkRadius?: number;
  sparkCount?: number;
  duration?: number;
  className?: string;
}

export default function ClickSpark({
  children,
  sparkColor = "#8b5cf6",
  sparkSize = 8,
  sparkRadius = 20,
  sparkCount = 8,
  duration = 400,
  className = "",
}: ClickSparkProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sparksRef = useRef<
    Array<{ x: number; y: number; angle: number; startTime: number }>
  >([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const parent = canvas.parentElement;
    if (!parent) return;

    const resize = () => {
      const { width, height } = parent.getBoundingClientRect();
      canvas.width = width;
      canvas.height = height;
    };

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(parent);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf: number;

    const draw = (ts: number) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      sparksRef.current = sparksRef.current.filter((spark) => {
        const elapsed = ts - spark.startTime;
        if (elapsed > duration) return false;

        const progress = elapsed / duration;
        const dist = sparkRadius * progress;
        const opacity = 1 - progress;

        const x = spark.x + Math.cos(spark.angle) * dist;
        const y = spark.y + Math.sin(spark.angle) * dist;

        ctx.beginPath();
        ctx.arc(x, y, sparkSize * (1 - progress) * 0.5, 0, Math.PI * 2);
        ctx.fillStyle = sparkColor;
        ctx.globalAlpha = opacity;
        ctx.fill();
        ctx.globalAlpha = 1;

        return true;
      });

      raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [sparkColor, sparkSize, sparkRadius, sparkCount, duration]);

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const now = performance.now();

      for (let i = 0; i < sparkCount; i++) {
        sparksRef.current.push({
          x,
          y,
          angle: (Math.PI * 2 * i) / sparkCount,
          startTime: now,
        });
      }
    },
    [sparkCount]
  );

  return (
    <div className={`relative ${className}`} onClick={handleClick}>
      <canvas
        ref={canvasRef}
        className="absolute inset-0 pointer-events-none"
        style={{ zIndex: 50 }}
      />
      {children}
    </div>
  );
}
