---
title: ClickSpark
summary: Source file components/bits/ClickSpark.tsx in the Next.js frontend
tags: []
related: []
keywords: []
createdAt: '2026-05-21T07:39:26.018Z'
updatedAt: '2026-05-21T07:39:26.018Z'
---
## Reason
Curate components/bits/ClickSpark.tsx from src folder

## Raw Concept
**Task:**
Document components/bits/ClickSpark.tsx

**Timestamp:** 2026-05-21

## Narrative
### Structure
Implementation for components/bits/ClickSpark.tsx

### Highlights
Captured complete source content from components/bits/ClickSpark.tsx

---


&quot;use client&quot;;

import { useRef, useEffect, useCallback } from &quot;react&quot;;

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
  sparkColor = &quot;#8b5cf6&quot;,
  sparkSize = 8,
  sparkRadius = 20,
  sparkCount = 8,
  duration = 400,
  className = &quot;&quot;,
}: ClickSparkProps) {
  const canvasRef = useRef&lt;HTMLCanvasElement&gt;(null);
  const sparksRef = useRef&lt;
    Array&lt;{ x: number; y: number; angle: number; startTime: number }&gt;
  &gt;([]);

  useEffect(() =&gt; {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const parent = canvas.parentElement;
    if (!parent) return;

    const resize = () =&gt; {
      const { width, height } = parent.getBoundingClientRect();
      canvas.width = width;
      canvas.height = height;
    };

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(parent);

    const ctx = canvas.getContext(&quot;2d&quot;);
    if (!ctx) return;

    let raf: number;

    const draw = (ts: number) =&gt; {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      sparksRef.current = sparksRef.current.filter((spark) =&gt; {
        const elapsed = ts - spark.startTime;
        if (elapsed &gt; duration) return false;

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

    return () =&gt; {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [sparkColor, sparkSize, sparkRadius, sparkCount, duration]);

  const handleClick = useCallback(
    (e: React.MouseEvent) =&gt; {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const now = performance.now();

      for (let i = 0; i &lt; sparkCount; i++) {
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
    &lt;div className={`relative ${className}`} onClick={handleClick}&gt;
      &lt;canvas
        ref={canvasRef}
        className=&quot;absolute inset-0 pointer-events-none&quot;
        style={{ zIndex: 50 }}
      /&gt;
      {children}
    &lt;/div&gt;
  );
}

    
