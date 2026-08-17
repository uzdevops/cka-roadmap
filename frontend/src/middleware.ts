import { NextResponse, type NextRequest } from 'next/server';

import {
  DEFAULT_LOCALE,
  isLocale,
  LOCALE_COOKIE,
  LOCALES,
  negotiateLocale,
} from '@/i18n/config';

/**
 * Every page lives under `/{locale}/...`. A request without a locale segment is
 * redirected to the visitor's preferred one: the cookie set by the language
 * switcher first, then Accept-Language, then the default.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const hasLocale = LOCALES.some(
    (locale) => pathname === `/${locale}` || pathname.startsWith(`/${locale}/`),
  );
  if (hasLocale) return NextResponse.next();

  const cookieLocale = request.cookies.get(LOCALE_COOKIE)?.value;
  const locale = isLocale(cookieLocale)
    ? cookieLocale
    : negotiateLocale(request.headers.get('accept-language'));

  const url = request.nextUrl.clone();
  url.pathname = `/${locale}${pathname === '/' ? '' : pathname}`;

  const response = NextResponse.redirect(url);
  if (!isLocale(cookieLocale)) {
    response.cookies.set(LOCALE_COOKIE, locale ?? DEFAULT_LOCALE, {
      path: '/',
      maxAge: 60 * 60 * 24 * 365,
      sameSite: 'lax',
    });
  }
  return response;
}

export const config = {
  // Skip Next internals, health probes, SEO files and anything with a file
  // extension - none of those are localised pages.
  matcher: ['/((?!_next|api|healthz|readyz|robots.txt|sitemap.xml|.*\\..*).*)'],
};
