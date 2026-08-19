import type { ReactNode } from 'react';

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

/**
 * Shared chrome for the lab pages. A lab is a terminal session on your own
 * cluster, so every lab surface opens with the same window strip: three dots,
 * the path you are standing in, and the difficulty of what is inside.
 */

/** The three window dots. Decoration only - hidden from assistive tech. */
export function TerminalDots() {
  return (
    <span className="lab-dots" aria-hidden>
      <span />
      <span />
      <span />
    </span>
  );
}

export function TerminalBar({
  path,
  children,
  className,
}: {
  path: string;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'flex items-center gap-2.5 border-b border-line bg-surface-2 px-3 py-2',
        className,
      )}
    >
      <TerminalDots />
      <span className="lab-path truncate">{path}</span>
      {children ? <span className="ml-auto flex items-center gap-2">{children}</span> : null}
    </div>
  );
}

/** Difficulty is a ramp, so it takes the status ramp - good, warning, serious.
 *  Never red: an advanced lab is hard, not broken. Unknown values fall back to
 *  the neutral outline, and the word itself is always printed. */
const DIFFICULTY_CLASS: Record<string, string> = {
  beginner: 'lab-difficulty-beginner',
  intermediate: 'lab-difficulty-intermediate',
  advanced: 'lab-difficulty-advanced',
};

export function DifficultyPill({
  difficulty,
  label,
  className,
}: {
  difficulty: string;
  label: string;
  className?: string;
}) {
  return (
    <Badge
      variant="outline"
      className={cn('lab-difficulty', DIFFICULTY_CLASS[difficulty], className)}
    >
      {label}
    </Badge>
  );
}

/** Estimated-time glyph. An SVG rather than an emoji so it inherits the text
 *  colour and renders identically on every platform. */
export function ClockIcon({ className }: { className?: string }) {
  return (
    <svg
      className={cn('h-3 w-3', className)}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      aria-hidden
    >
      <circle cx="8" cy="8" r="6.25" />
      <path d="M8 4.4V8l2.3 1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Section title with the accent tick. */
export function SectionHeading({ children }: { children: ReactNode }) {
  return (
    <h2 className="lab-heading text-lg font-semibold tracking-[-0.01em] text-ink">{children}</h2>
  );
}
