"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { Moon, Sun } from "lucide-react"
import { flushSync } from "react-dom"
import { useTheme } from "next-themes"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────

type ThemeToggleVariant = "default" | "pill" | "ghost"
type ThemeToggleSize = "sm" | "md" | "lg"

interface ThemeToggleProps extends React.ComponentPropsWithoutRef<"button"> {
  /** Visual style variant */
  variant?: ThemeToggleVariant
  /** Size of the toggle */
  size?: ThemeToggleSize
  /** Duration of the View Transition ripple (ms) */
  transitionDuration?: number
  /** Show label next to icon */
  showLabel?: boolean
}

// ─────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────

const SIZE_MAP: Record<ThemeToggleSize, { button: string; icon: string; label: string }> = {
  sm: { button: "h-8 w-8", icon: "h-3.5 w-3.5", label: "text-xs" },
  md: { button: "h-10 w-10", icon: "h-4 w-4", label: "text-sm" },
  lg: { button: "h-12 w-12", icon: "h-5 w-5", label: "text-base" },
}

const VARIANT_MAP: Record<ThemeToggleVariant, string> = {
  default: [
    "relative rounded-full border",
    "bg-background/80 border-border",
    "hover:bg-primary/10 hover:border-primary/30",
    "dark:bg-card dark:border-white/10",
    "dark:hover:bg-primary/20 dark:hover:border-primary/40",
    "shadow-sm hover:shadow-md",
    "backdrop-blur-sm",
  ].join(" "),
  pill: [
    "relative rounded-full border px-3",
    "bg-background/80 border-border",
    "hover:bg-primary/10 hover:border-primary/30",
    "dark:bg-card dark:border-white/10",
    "dark:hover:bg-primary/20 dark:hover:border-primary/40",
    "shadow-sm hover:shadow-md",
    "backdrop-blur-sm",
  ].join(" "),
  ghost: [
    "relative rounded-full",
    "hover:bg-primary/10 dark:hover:bg-primary/20",
  ].join(" "),
}

// ─────────────────────────────────────────────────────────────
// Icon animations (Magic UI-style spring)
// ─────────────────────────────────────────────────────────────

const iconVariants = {
  initial: { opacity: 0, scale: 0.5, rotate: -30, y: -4 },
  animate: { opacity: 1, scale: 1, rotate: 0, y: 0 },
  exit: { opacity: 0, scale: 0.5, rotate: 30, y: 4 },
}

const iconTransition = {
  type: "spring" as const,
  stiffness: 400,
  damping: 20,
}

// ─────────────────────────────────────────────────────────────
// Glow ring animation
// ─────────────────────────────────────────────────────────────

const GlowRing = ({ isDark }: { isDark: boolean }) => (
  <motion.span
    key={isDark ? "dark-ring" : "light-ring"}
    className={cn(
      "pointer-events-none absolute inset-[-3px] rounded-full",
      isDark
        ? "bg-gradient-to-tr from-violet-500/30 via-cyan-400/20 to-transparent"
        : "bg-gradient-to-tr from-amber-400/30 via-orange-300/20 to-transparent"
    )}
    initial={{ opacity: 0, scale: 0.8 }}
    animate={{ opacity: 1, scale: 1 }}
    exit={{ opacity: 0, scale: 1.1 }}
    transition={{ duration: 0.35, ease: "easeOut" }}
  />
)

// ─────────────────────────────────────────────────────────────
// ThemeToggle component
// ─────────────────────────────────────────────────────────────

export const ThemeToggle = ({
  className,
  variant = "default",
  size = "md",
  transitionDuration = 400,
  showLabel = false,
  ...props
}: ThemeToggleProps) => {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const buttonRef = useRef<HTMLButtonElement>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Avoid hydration mismatch: use theme before mount, resolvedTheme after
  const isDark = mounted ? resolvedTheme === "dark" : theme === "dark"

  const toggleTheme = useCallback(() => {
    const button = buttonRef.current
    if (!button) return

    const { top, left, width, height } = button.getBoundingClientRect()
    const x = left + width / 2
    const y = top + height / 2
    const vw = window.visualViewport?.width ?? window.innerWidth
    const vh = window.visualViewport?.height ?? window.innerHeight
    const maxRadius = Math.hypot(Math.max(x, vw - x), Math.max(y, vh - y))

    const newTheme: string = isDark ? "light" : "dark"
    const applyTheme = () => setTheme(newTheme)

    // Graceful degradation when View Transitions not supported
    if (typeof document.startViewTransition !== "function") {
      applyTheme()
      return
    }

    // Inject override styles to disable default crossfade
    const style = document.createElement("style")
    style.textContent = `
      ::view-transition-old(root),
      ::view-transition-new(root) {
        animation: none;
        mix-blend-mode: normal;
      }
      ::view-transition-new(root) { z-index: 999; }
    `
    document.head.appendChild(style)

    const transition = document.startViewTransition(() => {
      flushSync(applyTheme)
    })

    // Circular ripple from button centre
    transition.ready.then(() => {
      const keyframes = {
        clipPath: [
          `circle(0px at ${x}px ${y}px)`,
          `circle(${maxRadius}px at ${x}px ${y}px)`,
        ],
      }
      const timing: KeyframeAnimationOptions = {
        duration: transitionDuration,
        easing: "cubic-bezier(0.4, 0, 0.2, 1)",
      }

      document
        .querySelector("::view-transition-new(root)")
        ?.animate(keyframes, timing)

      document
        .querySelector("::view-transition-old(root)")
        ?.animate(
          {
            clipPath: [
              `circle(${maxRadius}px at ${x}px ${y}px)`,
              `circle(0px at ${x}px ${y}px)`,
            ],
          },
          timing
        )
    })

    transition.finished.finally(() => style.remove())
  }, [isDark, setTheme, transitionDuration])

  const sizes = SIZE_MAP[size]
  const isPill = variant === "pill"

  return (
    <button
      ref={buttonRef}
      id="theme-toggle"
      onClick={toggleTheme}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      aria-pressed={isDark}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className={cn(
        "inline-flex items-center justify-center gap-2",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "transition-all duration-200 ease-out",
        "cursor-pointer select-none",
        !isPill && sizes.button,
        VARIANT_MAP[variant],
        className
      )}
      {...props}
    >
      {/* Animated glow ring (behind icon) */}
      <AnimatePresence mode="wait">
        <GlowRing key={isDark ? "dark" : "light"} isDark={isDark} />
      </AnimatePresence>

      {/* Sun / Moon icon with spring animation */}
      <span className="relative z-10 flex items-center justify-center">
        <AnimatePresence mode="wait" initial={false}>
          {isDark ? (
            <motion.span
              key="moon"
              variants={iconVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={iconTransition}
              className="flex items-center justify-center text-violet-400 dark:text-violet-300"
            >
              <Moon className={sizes.icon} strokeWidth={2} />
            </motion.span>
          ) : (
            <motion.span
              key="sun"
              variants={iconVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={iconTransition}
              className="flex items-center justify-center text-amber-500"
            >
              <Sun className={sizes.icon} strokeWidth={2} />
            </motion.span>
          )}
        </AnimatePresence>
      </span>

      {/* Optional label */}
      {showLabel && (
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={isDark ? "dark-label" : "light-label"}
            initial={{ opacity: 0, x: -4 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 4 }}
            transition={{ duration: 0.2 }}
            className={cn(
              "relative z-10 font-medium tabular-nums",
              sizes.label,
              isDark ? "text-violet-300" : "text-amber-600"
            )}
          >
            {isDark ? "Dark" : "Light"}
          </motion.span>
        </AnimatePresence>
      )}
    </button>
  )
}

export default ThemeToggle
