"use client";

import { useEffect, useRef, useCallback } from "react";

interface ElectricBorderProps {
  children: React.ReactNode;
  color?: string;
  speed?: number;
  chaos?: number;
  borderRadius?: number;
  className?: string;
  style?: React.CSSProperties;
  active?: boolean;
}

export default function ElectricBorder({
  children,
  color = "#8b5cf6",
  speed = 1,
  chaos = 0.12,
  borderRadius = 16,
  className = "",
  style,
  active = true,
}: ElectricBorderProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>(0);

  const random = useCallback((x: number) => {
    return ((Math.sin(x * 12.9898) * 43758.5453) % 1 + 1) % 1;
  }, []);

  const noise2D = useCallback(
    (x: number, y: number) => {
      const i = Math.floor(x);
      const j = Math.floor(y);
      const fx = x - i;
      const fy = y - j;
      const a = random(i + j * 57);
      const b = random(i + 1 + j * 57);
      const c = random(i + (j + 1) * 57);
      const d = random(i + 1 + (j + 1) * 57);
      const ux = fx * fx * (3 - 2 * fx);
      const uy = fy * fy * (3 - 2 * fy);
      return a * (1 - ux) * (1 - uy) + b * ux * (1 - uy) + c * (1 - ux) * uy + d * ux * uy;
    },
    [random]
  );

  useEffect(() => {
    if (!active) return;
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let time = 0;

    const resize = () => {
      const rect = container.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      ctx.scale(dpr, dpr);
    };

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    const hexToRgb = (hex: string) => {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return { r, g, b };
    };

    const rgb = hexToRgb(color);

    const getPerimeterPoint = (t: number, w: number, h: number, r: number) => {
      const straightW = w - 2 * r;
      const straightH = h - 2 * r;
      const cornerArc = (Math.PI * r) / 2;
      const totalPerimeter = 2 * straightW + 2 * straightH + 4 * cornerArc;
      const distance = t * totalPerimeter;

      // Top edge
      if (distance < straightW) return { x: r + distance, y: 0 };
      // Top-right corner
      let acc = straightW;
      if (distance < acc + cornerArc) {
        const angle = ((distance - acc) / cornerArc) * (Math.PI / 2);
        return { x: w - r + r * Math.sin(angle), y: r - r * Math.cos(angle) };
      }
      // Right edge
      acc += cornerArc;
      if (distance < acc + straightH) return { x: w, y: r + (distance - acc) };
      // Bottom-right corner
      acc += straightH;
      if (distance < acc + cornerArc) {
        const angle = ((distance - acc) / cornerArc) * (Math.PI / 2);
        return { x: w - r + r * Math.cos(angle), y: h - r + r * Math.sin(angle) };
      }
      // Bottom edge
      acc += cornerArc;
      if (distance < acc + straightW) return { x: w - r - (distance - acc), y: h };
      // Bottom-left corner
      acc += straightW;
      if (distance < acc + cornerArc) {
        const angle = ((distance - acc) / cornerArc) * (Math.PI / 2);
        return { x: r - r * Math.sin(angle), y: h - r + r * Math.cos(angle) };
      }
      // Left edge
      acc += cornerArc;
      if (distance < acc + straightH) return { x: 0, y: h - r - (distance - acc) };
      // Top-left corner
      acc += straightH;
      const angle = ((distance - acc) / cornerArc) * (Math.PI / 2);
      return { x: r - r * Math.cos(angle), y: r - r * Math.sin(angle) };
    };

    const animate = () => {
      const rect = container.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;
      ctx.clearRect(0, 0, w, h);

      time += 0.016 * speed;

      // Draw electric border
      ctx.beginPath();
      const steps = 200;
      for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const base = getPerimeterPoint(t, w, h, borderRadius);
        const noise = (noise2D(t * 8, time * 3) - 0.5) * chaos * 20;
        const nx = base.x + noise * (base.y < h / 2 ? -1 : 1);
        const ny = base.y + noise * (base.x < w / 2 ? 1 : -1);
        if (i === 0) ctx.moveTo(nx, ny);
        else ctx.lineTo(nx, ny);
      }
      ctx.closePath();

      ctx.strokeStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.8)`;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Glow
      ctx.shadowColor = color;
      ctx.shadowBlur = 15;
      ctx.strokeStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.3)`;
      ctx.lineWidth = 4;
      ctx.stroke();
      ctx.shadowBlur = 0;

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationRef.current);
      ro.disconnect();
    };
  }, [active, color, speed, chaos, borderRadius, noise2D]);

  return (
    <div ref={containerRef} className={`relative ${className}`} style={style}>
      {active && (
        <canvas
          ref={canvasRef}
          className="absolute inset-0 pointer-events-none"
          style={{ zIndex: 1 }}
        />
      )}
      <div className="relative z-[2]">{children}</div>
    </div>
  );
}
