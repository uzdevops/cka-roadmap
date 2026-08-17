import { cva, type VariantProps } from 'class-variance-authority';
import Link from 'next/link';
import { forwardRef, type ButtonHTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 whitespace-nowrap',
  {
    variants: {
      variant: {
        primary: 'bg-[var(--accent)] text-[var(--accent-ink)] hover:opacity-90',
        secondary:
          'bg-[var(--surface-2)] text-ink border border-line hover:bg-[var(--surface-1)]',
        outline: 'border border-line text-ink hover:bg-[var(--surface-2)]',
        ghost: 'text-ink-secondary hover:bg-[var(--surface-2)] hover:text-ink',
        danger: 'bg-[var(--critical)] text-white hover:opacity-90',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4 text-sm',
        lg: 'h-11 px-6 text-base',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  ),
);
Button.displayName = 'Button';

export function ButtonLink({
  className,
  variant,
  size,
  href,
  children,
  ...props
}: VariantProps<typeof buttonVariants> & {
  href: string;
  className?: string;
  children: React.ReactNode;
} & Omit<React.ComponentProps<typeof Link>, 'href' | 'className'>) {
  return (
    <Link href={href} className={cn(buttonVariants({ variant, size }), className)} {...props}>
      {children}
    </Link>
  );
}

export { buttonVariants };
