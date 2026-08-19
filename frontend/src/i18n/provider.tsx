'use client';

import { usePathname } from 'next/navigation';
import { createContext, useContext, useMemo, type ReactNode } from 'react';

import { setApiLocale, setApiTrack } from '@/lib/api';
import {
  DEFAULT_TRACK,
  trackFromPathname,
  trackPath,
  type TrackSlug,
} from '@/tracks/config';

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
  track,
  children,
}: {
  locale: Locale;
  track?: TrackSlug;
  children: ReactNode;
}) {
  // The app shell - and with it the whole navigation rail - is mounted by the
  // LOCALE layout, which sits above the [track] segment and so is never handed
  // a track. Reading it off the URL is what stops every rail link pointing at
  // the default track no matter which one you are actually looking at.
  const pathname = usePathname();
  const active = track ?? trackFromPathname(pathname ?? '') ?? DEFAULT_TRACK;
  // Set synchronously during render so the first API call of a page already
  // carries the right ?lang= and ?track=, rather than one render behind.
  setApiLocale(locale);
  setApiTrack(active);

  const value = useMemo<I18nValue>(
    () => ({
      locale,
      track: active,
      t: getDictionary(locale),
      href: (path: string) => trackPath(path, locale, active),
      fill,
    }),
    [locale, active],
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
