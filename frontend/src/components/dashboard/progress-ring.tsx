/**
 * The dashboard's hero figure: one value, drawn as a ring.
 *
 * Hand-built SVG like the rest of the charts. The number is real text on top of
 * the ring rather than `<text>` inside it, so it stays crisp, picks up the
 * app's font, and never needs re-measuring when a translation is longer.
 */
export function ProgressRing({
  value,
  label,
  caption,
  size = 176,
  thickness = 14,
}: {
  value: number;
  /** Accessible name for the figure - the ring itself is one `img` to AT. */
  label: string;
  caption?: string;
  size?: number;
  thickness?: number;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped / 100);

  return (
    <div
      className="relative shrink-0"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`${label}: ${Math.round(clamped)}%`}
    >
      <svg viewBox={`0 0 ${size} ${size}`} className="h-full w-full -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={thickness}
          stroke="var(--track)"
        />
        <circle
          className="dash-ring-fill"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={thickness}
          stroke="var(--accent)"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-4xl font-semibold leading-none tracking-tight text-ink tabular-nums">
          {Math.round(clamped)}
          <span className="ml-0.5 text-xl font-medium text-ink-muted">%</span>
        </span>
        {caption && (
          <span className="mt-1.5 max-w-[70%] text-[11px] font-medium uppercase leading-tight tracking-wide text-ink-muted">
            {caption}
          </span>
        )}
      </div>
    </div>
  );
}
