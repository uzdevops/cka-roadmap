import { cva, type VariantProps } from 'class-variance-authority';
import type { HTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.08em]',
  {
    variants: {
      variant: {
        neutral: 'border-line bg-[var(--surface-2)] text-ink-secondary',
        accent: 'border-transparent bg-[var(--accent-badge-bg)] text-[var(--accent-badge-text)]',
        good: 'badge-good border-transparent text-[var(--good-text)]',
        warning: 'badge-warning border-transparent text-[var(--warning)]',
        critical: 'badge-critical border-transparent text-[var(--critical)]',
        live: 'badge-good border-transparent text-[var(--good-text)]',
        outline: 'border-line text-ink-muted',
      },
    },
    defaultVariants: { variant: 'neutral' },
  },
);

export function Badge({
  className,
  variant,
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props}>
      {/* `live` marks the thing happening right now - the pulse is the point. */}
      {variant === 'live' && <span aria-hidden className="badge-live-dot" />}
      {children}
    </span>
  );
}
