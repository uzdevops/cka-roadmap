import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '-';
  return new Date(value).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatMinutes(minutes: number, unit = 'min'): string {
  if (minutes < 60) return `${minutes} ${unit}`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours}h ${rest}m` : `${hours}h`;
}

/** Locale-aware date, used for anything the user reads rather than sorts. */
export function formatDateLocale(
  value: string | null | undefined,
  locale: string,
): string {
  if (!value) return '-';
  return new Date(value).toLocaleDateString(locale === 'uz' ? 'uz-UZ' : 'en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/** Categorical slot for a phase, by its 1-based order. Fixed order, never cycled. */
export function phaseColor(orderIndex: number): string {
  const slot = Math.min(Math.max(orderIndex, 1), 6);
  return `var(--series-${slot})`;
}

export function pluralize(count: number, singular: string, plural?: string): string {
  return `${count} ${count === 1 ? singular : (plural ?? `${singular}s`)}`;
}
