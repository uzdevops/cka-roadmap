import { NextResponse, type NextRequest } from 'next/server';

import {
  DEFAULT_LOCALE,
  isLocale,
  LOCALE_COOKIE,
  LOCALES,
  negotiateLocale,
} from '@/i18n/config';
import { ACCESS_COOKIE } from '@/lib/api';
import {
  DEFAULT_TRACK,
  isTrack,
  isTrackSection,
  isTracklessPath,
  TRACK_COOKIE,
} from '@/tracks/config';

/** Reachable without an account. Everything else needs one. */
const PUBLIC_PATHS = ['/login', '/admin/login', '/auth/callback'];

function stripLocalePrefix(pathname: string): string {
  for (const locale of LOCALES) {
    if (pathname === `/${locale}`) return '/';
    if (pathname.startsWith(`/${locale}/`)) return pathname.slice(locale.length + 1);
  }
  return pathname;
}

/** "/cka/lessons" -> "/lessons". Used only to test what a path is ABOUT. */
function stripTrackPrefix(pathname: string): string {
  const [, first, ...rest] = pathname.split('/');
  if (!isTrack(first)) return pathname;
  const tail = rest.join('/');
  return tail ? `/${tail}` : '/';
}

/**
 * Three jobs, in this order.
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
 *
 * 3. **The track.** Content pages live under `/{locale}/{track}/...`. A request
 *    that names no track is sent to the last one they used, or the default.
 *    Signing in, the profile, the admin panel and the track picker itself stay
 *    outside that segment - none of them is about one programme of study.
 *
 * The order matters: the login redirect has to happen before any track is
 * invented, or an anonymous visitor gets bounced twice and arrives at the login
 * screen having lost where they were going.
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

  const cookieTrack = request.cookies.get(TRACK_COOKIE)?.value;
  const track = isTrack(cookieTrack) ? cookieTrack : DEFAULT_TRACK;

  const bare = stripLocalePrefix(pathname);
  // What the path is about, with both prefixes removed - so `/uz/cka/lessons`
  // and `/lessons` are recognised as the same destination.
  const withoutTrack = stripTrackPrefix(bare);
  const isPublic = PUBLIC_PATHS.some(
    (p) => withoutTrack === p || withoutTrack.startsWith(`${p}/`),
  );
  const signedIn = Boolean(request.cookies.get(ACCESS_COOKIE)?.value);

  if (!signedIn && !isPublic) {
    const url = request.nextUrl.clone();
    // Each surface has its own door: a signed-out visit to the console is
    // sent to the console's sign-in, not the student one.
    const door = bare === '/admin' || bare.startsWith('/admin/') ? '/admin/login' : '/login';
    url.pathname = `/${locale}${door}`;
    // So the login page can bounce them back where they were headed. The
    // locale-stripped path - which still carries the track, so they return to
    // the right one.
    if (bare !== '/') url.searchParams.set('next', bare);
    return NextResponse.redirect(url);
  }

  // Signed in and standing on a login page: nothing to do there. Each door
  // forwards to its own surface; whether the account may actually enter the
  // console is the guard's question, which owns the refusal screen.
  if (signedIn && withoutTrack === '/login') {
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}/${track}/dashboard`;
    url.search = '';
    return NextResponse.redirect(url);
  }
  if (signedIn && withoutTrack === '/admin/login') {
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}/admin`;
    url.search = '';
    return NextResponse.redirect(url);
  }

  if (!hasLocale) {
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

  // Locale is settled. Only a path that NAMES a track section gets one
  // prepended - that is an old bookmark like /en/lessons. Anything else with an
  // unrecognised first segment falls through to Next, where the [track] layout
  // 404s it; prepending there would turn a typo into /en/cka/nope/lessons,
  // which is neither the page asked for nor an error.
  const firstSegment = bare.split('/')[1] ?? '';

  if (isTrackSection(firstSegment) && !isTrack(firstSegment)) {
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}/${track}${bare}`;
    return NextResponse.redirect(url);
  }

  // Remember the track that is actually being used, so /{locale} and a later
  // visit land where they left off. The URL stays the source of truth; this is
  // only the default - the same relationship LOCALE_COOKIE has with the locale
  // segment.
  const response = NextResponse.next();
  if (isTrack(firstSegment) && firstSegment !== cookieTrack) {
    response.cookies.set(TRACK_COOKIE, firstSegment, {
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
