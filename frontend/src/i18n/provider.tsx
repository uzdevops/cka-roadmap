'use client';

import { createContext, useContext, useMemo, type ReactNode } from 'react';

import { setApiLocale, setApiTrack } from '@/lib/api';
import { DEFAULT_TRACK, trackPath, type TrackSlug } from '@/tracks/config';

import { DEFAULT_LOCALE, type Locale } from '@/i18n/config';
import { fill, getDictionary, type Dictionary } from '@/i18n';

interface I18nValue {
  locale: Locale;
  track: TrackSlug;
  t: Dictionary;
  /**
   * Prefixes an app path with the active locale AND track:
   * ("/lessons") -> "/uz/docker/lessons".
   *
   * The track lives here rather than in a provider of its own because this is
   * the single function that ~40 link sites already go through. Routes that are
   * not about one programme of study - signing in, the profile, the admin panel
   * - are passed through with the locale only; `trackPath` knows which those
   * are.
   */
  href: (path: string) => string;
  fill: typeof fill;
}

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({
  locale,
  track = DEFAULT_TRACK,
  children,
}: {
  locale: Locale;
  track?: TrackSlug;
  children: ReactNode;
}) {
  // Set synchronously during render so the first API call of a page already
  // carries the right ?lang= and ?track=, rather than one render behind.
  setApiLocale(locale);
  setApiTrack(track);

  const value = useMemo<I18nValue>(
    () => ({
      locale,
      track,
      t: getDictionary(locale),
      href: (path: string) => trackPath(path, locale, track),
      fill,
    }),
    [locale, track],
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
      track: DEFAULT_TRACK,
      t: getDictionary(DEFAULT_LOCALE),
      href: (path: string) => trackPath(path, DEFAULT_LOCALE, DEFAULT_TRACK),
      fill,
    };
  }
  return ctx;
}
