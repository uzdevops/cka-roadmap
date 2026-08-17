import { NextResponse, type NextRequest } from 'next/server';

import {
  DEFAULT_LOCALE,
  isLocale,
  LOCALE_COOKIE,
  LOCALES,
  negotiateLocale,
} from '@/i18n/config';
import { ACCESS_COOKIE } from '@/lib/api';

/** Reachable without an account. Everything else needs one. */
const PUBLIC_PATHS = ['/login', '/auth/callback'];

function stripLocalePrefix(pathname: string): string {
  for (const locale of LOCALES) {
    if (pathname === `/${locale}`) return '/';
    if (pathname.startsWith(`/${locale}/`)) return pathname.slice(locale.length + 1);
  }
  return pathname;
}

/**
 * Two jobs, in this order.
 *
 * 1. **The gate.** The platform is closed: without a session cookie every page
 *    redirects to the login screen. This is why tokens moved out of
 *    localStorage - middleware runs on the server and can only read cookies.
 *    It is a first line, not the only one: the API refuses anonymous callers
 *    independently, so a forged cookie buys nothing.
 *
 * 2. **The locale.** Every page lives under `/{locale}/...`, so a request
 *    without one is redirected to the visitor's preferred language - the cookie
 *    set by the switcher first, then Accept-Language, then the default.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const hasLocale = LOCALES.some(
    (locale) => pathname === `/${locale}` || pathname.startsWith(`/${locale}/`),
  );

  const cookieLocale = request.cookies.get(LOCALE_COOKIE)?.value;
  const locale = isLocale(cookieLocale)
    ? cookieLocale
    : negotiateLocale(request.headers.get('accept-language'));

  const bare = stripLocalePrefix(pathname);
  const isPublic = PUBLIC_PATHS.some((p) => bare === p || bare.startsWith(`${p}/`));
  const signedIn = Boolean(request.cookies.get(ACCESS_COOKIE)?.value);

  if (!signedIn && !isPublic) {
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}/login`;
    // So the login page can bounce them back where they were headed. The
    // locale-stripped path, because the login page prefixes the locale itself.
    if (bare !== '/') url.searchParams.set('next', bare);
    return NextResponse.redirect(url);
  }

  // Signed in and standing on the login page: nothing to do there.
  if (signedIn && bare === '/login') {
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}`;
    url.search = '';
    return NextResponse.redirect(url);
  }

  if (hasLocale) return NextResponse.next();

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
  // extension - none of those are localised pages. `/admin` is deliberately NOT
  // excluded: it falls through to the locale redirect above and lands on
  // `/{locale}/admin`, which is what makes /admin a working entry point.
  matcher: ['/((?!_next|api|healthz|readyz|robots.txt|sitemap.xml|.*\\..*).*)'],
};
