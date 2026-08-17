import { cn } from '@/lib/utils';

/**
 * A single-value meter. The track is a lighter step of the fill's own ramp so
 * the state reads across the whole bar, per the mark spec.
 */
export function Meter({
  value,
  label,
  className,
  height = 8,
}: {
  value: number;
  label?: string;
  className?: string;
  height?: number;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div
      className={cn('w-full overflow-hidden rounded-full', className)}
      style={{ background: 'var(--track)', height }}
      role="meter"
      aria-valuenow={Math.round(clamped)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
    >
      <div
        className="h-full rounded-full transition-[width] duration-500"
        style={{ width: `${clamped}%`, background: 'var(--accent)' }}
      />
    </div>
  );
}
