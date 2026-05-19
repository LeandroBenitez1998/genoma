"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import { useInView, useMotionValue, useSpring } from "framer-motion";

interface CountUpProps {
  to: number;
  from?: number;
  direction?: "up" | "down";
  delay?: number;
  duration?: number;
  className?: string;
  separator?: string;
  onStart?: () => void;
  onEnd?: () => void;
}

export default function CountUp({
  to,
  from = 0,
  direction = "up",
  delay = 0,
  duration = 2,
  className = "",
  separator = "",
  onStart,
  onEnd,
}: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const motionValue = useMotionValue(direction === "down" ? to : from);
  const damping = 20 + 40 * (1 / duration);
  const stiffness = 100 * (1 / duration);
  const springValue = useSpring(motionValue, { damping, stiffness });
  const isInView = useInView(ref, { once: true, margin: "0px" });
  const [displayValue, setDisplayValue] = useState<string>(
    () => formatValue(direction === "down" ? to : from, from, to, separator)
  );

  const maxDecimals = Math.max(
    getDecimalPlaces(from),
    getDecimalPlaces(to)
  );

  // Spring animation → state update (never mutates DOM)
  useEffect(() => {
    const unsubscribe = springValue.on("change", (latest) => {
      setDisplayValue(formatValue(latest, from, to, separator));
    });
    return unsubscribe;
  }, [springValue, from, to, separator]);

  // Trigger animation on enter viewport
  useEffect(() => {
    if (isInView) {
      onStart?.();
      const timeout = setTimeout(() => {
        motionValue.set(direction === "down" ? from : to);
      }, delay * 1000);
      const endTimeout = setTimeout(() => {
        onEnd?.();
      }, delay * 1000 + duration * 1000);
      return () => {
        clearTimeout(timeout);
        clearTimeout(endTimeout);
      };
    }
  }, [isInView, from, to, direction, delay, duration, motionValue, onStart, onEnd]);

  return <span ref={ref} className={className}>{displayValue}</span>;
}

// ── Helpers ──

function getDecimalPlaces(num: number): number {
  const str = num.toString();
  if (str.includes(".")) {
    const decimals = str.split(".")[1];
    if (parseInt(decimals) !== 0) return decimals.length;
  }
  return 0;
}

function formatValue(
  value: number,
  from: number,
  to: number,
  separator: string
): string {
  const maxDecimals = Math.max(getDecimalPlaces(from), getDecimalPlaces(to));
  const hasDecimals = maxDecimals > 0;
  const options: Intl.NumberFormatOptions = {
    useGrouping: !!separator,
    minimumFractionDigits: hasDecimals ? maxDecimals : 0,
    maximumFractionDigits: hasDecimals ? maxDecimals : 0,
  };
  const formatted = new Intl.NumberFormat("en-US", options).format(value);
  return separator ? formatted.replace(/,/g, separator) : formatted;
}
