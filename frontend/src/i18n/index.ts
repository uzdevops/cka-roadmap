import { en, type Dictionary } from '@/i18n/dictionaries/en';
import { uz } from '@/i18n/dictionaries/uz';
import { DEFAULT_LOCALE, type Locale } from '@/i18n/config';

const DICTIONARIES: Record<Locale, Dictionary> = { en, uz };

export function getDictionary(locale: Locale): Dictionary {
  return DICTIONARIES[locale] ?? DICTIONARIES[DEFAULT_LOCALE];
}

/**
 * Fills `{placeholders}` in a dictionary string.
 *
 *   t('{done} of {total}', { done: 3, total: 10 })  ->  "3 of 10"
 */
export function fill(
  template: string,
  values: Record<string, string | number>,
): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) =>
    key in values ? String(values[key]) : match,
  );
}

export type { Dictionary };
