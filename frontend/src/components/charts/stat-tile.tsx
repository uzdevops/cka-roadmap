import type { ReactNode } from 'react';

import { cn } from '@/lib/utils';

/**
 * Stat tile: label (sentence case) - value (semibold, proportional figures) -
 * optional hint. Never a one-bar bar chart; the number is the chart.
 */
export function StatTile({
  label,
  value,
  hint,
  tone = 'default',
  className,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: 'default' | 'good' | 'critical';
  className?: string;
}) {
  const valueColor =
    tone === 'good'
      ? 'var(--good-text)'
      : tone === 'critical'
        ? 'var(--critical)'
        : 'var(--text-primary)';

  return (
    <div className={cn('rounded-card border border-line bg-surface p-4', className)}>
      <p className="tech-label">{label}</p>
      <p className="mt-2 text-2xl font-bold leading-none tracking-[-0.01em]" style={{ color: valueColor }}>
        {value}
      </p>
      {hint && <p className="mt-2 text-xs text-ink-secondary">{hint}</p>}
    </div>
  );
}
