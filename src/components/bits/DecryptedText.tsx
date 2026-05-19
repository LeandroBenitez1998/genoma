"use client";

import { useEffect, useState, useRef, useMemo, useCallback } from "react";
import { motion } from "framer-motion";

interface DecryptedTextProps {
  text: string;
  speed?: number;
  maxIterations?: number;
  sequential?: boolean;
  revealDirection?: "start" | "end" | "center";
  useOriginalCharsOnly?: boolean;
  characters?: string;
  className?: string;
  parentClassName?: string;
  encryptedClassName?: string;
  animateOn?: "hover" | "view" | "click";
}

export default function DecryptedText({
  text,
  speed = 50,
  maxIterations = 10,
  sequential = false,
  revealDirection = "start",
  useOriginalCharsOnly = false,
  characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+",
  className = "",
  parentClassName = "",
  encryptedClassName = "",
  animateOn = "hover",
}: DecryptedTextProps) {
  const [displayText, setDisplayText] = useState(text);
  const [isAnimating, setIsAnimating] = useState(false);
  const [revealedIndices, setRevealedIndices] = useState<Set<number>>(new Set());
  const containerRef = useRef<HTMLSpanElement>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const availableChars = useMemo(() => {
    return useOriginalCharsOnly
      ? Array.from(new Set(text.split(""))).filter((c) => c !== " ")
      : characters.split("");
  }, [useOriginalCharsOnly, text, characters]);

  const shuffleText = useCallback(
    (original: string, revealed: Set<number>) => {
      return original
        .split("")
        .map((char, i) => {
          if (char === " ") return " ";
          if (revealed.has(i)) return original[i];
          return availableChars[Math.floor(Math.random() * availableChars.length)];
        })
        .join("");
    },
    [availableChars]
  );

  const getOrder = useCallback(
    (len: number) => {
      const order: number[] = [];
      if (revealDirection === "start") {
        for (let i = 0; i < len; i++) order.push(i);
      } else if (revealDirection === "end") {
        for (let i = len - 1; i >= 0; i--) order.push(i);
      } else {
        const mid = Math.floor(len / 2);
        order.push(mid);
        for (let i = 1; i <= mid; i++) {
          if (mid - i >= 0) order.push(mid - i);
          if (mid + i < len) order.push(mid + i);
        }
      }
      return order;
    },
    [revealDirection]
  );

  const startAnimation = useCallback(() => {
    if (isAnimating) return;
    setIsAnimating(true);
    setRevealedIndices(new Set());

    let iteration = 0;
    const order = getOrder(text.length);

    intervalRef.current = setInterval(() => {
      if (sequential) {
        setRevealedIndices((prev) => {
          const next = new Set(prev);
          const nextIdx = order[next.size];
          if (nextIdx !== undefined) next.add(nextIdx);
          if (next.size >= text.length) {
            clearInterval(intervalRef.current!);
            setIsAnimating(false);
          }
          return next;
        });
      } else {
        iteration++;
        const revealed = new Set<number>();
        const numToReveal = Math.floor((iteration / maxIterations) * text.length);
        for (let i = 0; i < numToReveal && i < order.length; i++) {
          revealed.add(order[i]);
        }
        setRevealedIndices(revealed);
        if (iteration >= maxIterations) {
          clearInterval(intervalRef.current!);
          setIsAnimating(false);
        }
      }
    }, speed);
  }, [isAnimating, text, sequential, maxIterations, speed, getOrder]);

  useEffect(() => {
    if (animateOn === "view") {
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) startAnimation();
        },
        { threshold: 0.1 }
      );
      if (containerRef.current) observer.observe(containerRef.current);
      return () => observer.disconnect();
    }
  }, [animateOn, startAnimation]);

  useEffect(() => {
    if (isAnimating) {
      setDisplayText(shuffleText(text, revealedIndices));
    } else if (revealedIndices.size === 0 && animateOn !== "view") {
      setDisplayText(text);
    } else {
      setDisplayText(
        text
          .split("")
          .map((c, i) => (revealedIndices.has(i) ? c : c === " " ? " " : availableChars[Math.floor(Math.random() * availableChars.length)]))
          .join("")
      );
    }
  }, [isAnimating, revealedIndices, text, shuffleText, availableChars, animateOn]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return (
    <motion.span
      ref={containerRef}
      className={`inline-block whitespace-pre-wrap ${parentClassName}`}
      onMouseEnter={animateOn === "hover" ? startAnimation : undefined}
      onClick={animateOn === "click" ? startAnimation : undefined}
    >
      <span className={isAnimating ? encryptedClassName : className}>
        {displayText}
      </span>
    </motion.span>
  );
}
