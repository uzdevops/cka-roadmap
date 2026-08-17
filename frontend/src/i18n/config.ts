export const LOCALES = ['en', 'uz'] as const;

export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale =
  (process.env.NEXT_PUBLIC_DEFAULT_LOCALE as Locale | undefined) ?? 'en';

export const LOCALE_COOKIE = 'NEXT_LOCALE';

export const LOCALE_LABELS: Record<Locale, string> = {
  en: 'English',
  uz: "O'zbekcha",
};

/** Short badge shown in the switcher. */
export const LOCALE_SHORT: Record<Locale, string> = {
  en: 'EN',
  uz: 'UZ',
};

export function isLocale(value: string | undefined | null): value is Locale {
  return !!value && (LOCALES as readonly string[]).includes(value);
}

export function normalizeLocale(value: string | undefined | null): Locale {
  if (!value) return DEFAULT_LOCALE;
  const base = value.trim().toLowerCase().replace('_', '-').split('-')[0];
  return isLocale(base) ? base : DEFAULT_LOCALE;
}

/** Picks the first supported language out of an Accept-Language header. */
export function negotiateLocale(acceptLanguage: string | null): Locale {
  if (!acceptLanguage) return DEFAULT_LOCALE;
  const tags = acceptLanguage
    .split(',')
    .map((part) => {
      const [tag, q] = part.trim().split(';q=');
      return { tag: tag.trim(), q: q ? Number(q) : 1 };
    })
    .sort((a, b) => b.q - a.q);

  for (const { tag } of tags) {
    const base = tag.toLowerCase().split('-')[0];
    if (isLocale(base)) return base;
  }
  return DEFAULT_LOCALE;
}

/** Prefixes an app path with the active locale: ("/lessons", "uz") -> "/uz/lessons". */
export function localePath(path: string, locale: Locale): string {
  const clean = path.startsWith('/') ? path : `/${path}`;
  return clean === '/' ? `/${locale}` : `/${locale}${clean}`;
}

/** Strips the locale segment back off: "/uz/lessons" -> "/lessons". */
export function stripLocale(pathname: string): string {
  const segments = pathname.split('/');
  if (isLocale(segments[1])) {
    const rest = segments.slice(2).join('/');
    return rest ? `/${rest}` : '/';
  }
  return pathname || '/';
}
