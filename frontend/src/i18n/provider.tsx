'use client';

import { createContext, useContext, useMemo, type ReactNode } from 'react';

import { setApiLocale } from '@/lib/api';

import { DEFAULT_LOCALE, localePath, type Locale } from '@/i18n/config';
import { fill, getDictionary, type Dictionary } from '@/i18n';

interface I18nValue {
  locale: Locale;
  t: Dictionary;
  /** Prefixes an app path with the active locale. */
  href: (path: string) => string;
  fill: typeof fill;
}

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({
  locale,
  children,
}: {
  locale: Locale;
  children: ReactNode;
}) {
  // Set synchronously during render so the first API call of a page already
  // carries the right ?lang=, rather than one render behind.
  setApiLocale(locale);

  const value = useMemo<I18nValue>(
    () => ({
      locale,
      t: getDictionary(locale),
      href: (path: string) => localePath(path, locale),
      fill,
    }),
    [locale],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    // Should never happen inside the [locale] tree, but keeps client
    // components renderable in isolation (tests, storybook).
    return {
      locale: DEFAULT_LOCALE,
      t: getDictionary(DEFAULT_LOCALE),
      href: (path: string) => localePath(path, DEFAULT_LOCALE),
      fill,
    };
  }
  return ctx;
}
