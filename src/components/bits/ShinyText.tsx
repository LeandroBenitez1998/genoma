"use client";

import { useRef, useEffect } from "react";

export default function ShinyText({
  text,
  disabled = false,
  speed = 3,
  className = "",
  color = "#a1a1aa",
  shineColor = "#ffffff",
}: {
  text: string;
  disabled?: boolean;
  speed?: number;
  className?: string;
  color?: string;
  shineColor?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (disabled || !ref.current) return;
    let pos = -100;
    let raf: number;

    const animate = () => {
      pos += 0.5;
      if (pos > 200) pos = -100;
      if (ref.current) {
        ref.current.style.backgroundPosition = `${pos}% 0`;
      }
      raf = requestAnimationFrame(animate);
    };

    animate();
    return () => cancelAnimationFrame(raf);
  }, [disabled, speed]);

  return (
    <span
      ref={ref}
      className={`inline-block bg-clip-text text-transparent ${className}`}
      style={{
        color: disabled ? color : undefined,
        backgroundImage: disabled
          ? undefined
          : `linear-gradient(90deg, ${color} 0%, ${color} 40%, ${shineColor} 50%, ${color} 60%, ${color} 100%)`,
        backgroundSize: "200% 100%",
      }}
    >
      {text}
    </span>
  );
}
