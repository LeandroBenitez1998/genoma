"use client";

import { useEffect, useRef, useState, useCallback } from "react";

interface TextTypeProps {
  text: string[];
  typingSpeed?: number;
  pauseDuration?: number;
  deletingSpeed?: number;
  loop?: boolean;
  className?: string;
  showCursor?: boolean;
  cursorCharacter?: string;
}

export default function TextType({
  text: textArray,
  typingSpeed = 40,
  pauseDuration = 2000,
  deletingSpeed = 20,
  loop = true,
  className = "",
  showCursor = true,
  cursorCharacter = "▊",
}: TextTypeProps) {
  const [displayText, setDisplayText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const currentText = textArray[currentIndex] || "";

  const tick = useCallback(() => {
    if (isPaused) {
      timeoutRef.current = setTimeout(() => {
        setIsPaused(false);
        setIsDeleting(true);
      }, pauseDuration);
      return;
    }

    if (!isDeleting) {
      // Typing
      if (displayText.length < currentText.length) {
        setDisplayText(currentText.slice(0, displayText.length + 1));
        timeoutRef.current = setTimeout(tick, typingSpeed);
      } else {
        setIsPaused(true);
        timeoutRef.current = setTimeout(tick, 0);
      }
    } else {
      // Deleting
      if (displayText.length > 0) {
        setDisplayText(displayText.slice(0, -1));
        timeoutRef.current = setTimeout(tick, deletingSpeed);
      } else {
        setIsDeleting(false);
        const next = (currentIndex + 1) % textArray.length;
        if (next === 0 && !loop) return;
        setCurrentIndex(next);
        timeoutRef.current = setTimeout(tick, typingSpeed);
      }
    }
  }, [
    displayText,
    currentText,
    currentIndex,
    isDeleting,
    isPaused,
    textArray,
    typingSpeed,
    deletingSpeed,
    pauseDuration,
    loop,
  ]);

  useEffect(() => {
    timeoutRef.current = setTimeout(tick, typingSpeed);
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [tick, typingSpeed]);

  return (
    <span className={className}>
      {displayText}
      {showCursor && (
        <span className="inline-block animate-pulse ml-0.5 text-accent-violet">
          {cursorCharacter}
        </span>
      )}
    </span>
  );
}
