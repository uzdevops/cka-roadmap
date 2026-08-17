'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';

import {
  LOCALE_COOKIE,
  LOCALE_LABELS,
  LOCALE_SHORT,
  LOCALES,
  localePath,
  stripLocale,
  type Locale,
} from '@/i18n/config';
import { useI18n } from '@/i18n/provider';
import { cn } from '@/lib/utils';

/**
 * Switches language by navigating to the same page under the other locale
 * prefix, and remembers the choice in a cookie so the middleware honours it on
 * the next visit.
 */
export function LanguageSwitcher() {
  const { locale, t } = useI18n();
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  const choose = (next: Locale) => {
    document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=${60 * 60 * 24 * 365}; samesite=lax`;
    setOpen(false);
    router.push(localePath(stripLocale(pathname), next));
    router.refresh();
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        onBlur={() => window.setTimeout(() => setOpen(false), 120)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`${t.common.language}: ${LOCALE_LABELS[locale]}`}
        className="flex h-9 items-center gap-1 rounded-lg border border-line px-2.5 text-xs font-semibold tracking-wide text-ink-secondary transition-colors hover:bg-[var(--surface-2)] hover:text-ink"
      >
        {LOCALE_SHORT[locale]}
        <span aria-hidden className="text-[10px] leading-none">
          ▾
        </span>
      </button>

      {open && (
        <ul
          role="listbox"
          className="absolute right-0 z-50 mt-1 min-w-36 overflow-hidden rounded-lg border border-line bg-surface py-1 shadow-lg"
        >
          {LOCALES.map((option) => (
            <li key={option}>
              <button
                type="button"
                role="option"
                aria-selected={option === locale}
                onMouseDown={(event) => {
                  event.preventDefault();
                  choose(option);
                }}
                className={cn(
                  'flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm transition-colors hover:bg-[var(--surface-2)]',
                  option === locale ? 'text-ink' : 'text-ink-secondary',
                )}
              >
                {LOCALE_LABELS[option]}
                {option === locale && (
                  <span aria-hidden className="text-[var(--accent)]">
                    ✓
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
