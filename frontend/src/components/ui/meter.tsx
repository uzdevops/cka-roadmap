import { cn } from '@/lib/utils';

/**
 * A single-value meter. The track is a lighter step of the fill's own ramp so
 * the state reads across the whole bar, per the mark spec.
 */
export function Meter({
  value,
  label,
  className,
  height = 6,
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
        className="meter-fill h-full rounded-full"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
