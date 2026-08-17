import { cva, type VariantProps } from 'class-variance-authority';
import type { HTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
  {
    variants: {
      variant: {
        neutral: 'border-line bg-[var(--surface-2)] text-ink-secondary',
        accent: 'border-transparent bg-[var(--accent-badge-bg)] text-[var(--accent-badge-text)]',
        good: 'border-transparent bg-[var(--surface-2)] text-[var(--good-text)]',
        warning: 'border-transparent bg-[var(--surface-2)] text-ink-secondary',
        critical: 'border-transparent bg-[var(--surface-2)] text-[var(--critical)]',
        outline: 'border-line text-ink-muted',
      },
    },
    defaultVariants: { variant: 'neutral' },
  },
);

export function Badge({
  className,
  variant,
  ...props
}: HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
