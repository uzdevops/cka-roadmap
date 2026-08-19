/**
 * The programmes of study, as far as ROUTING is concerned.
 *
 * Tracks are database rows - their titles, summaries and links all come from the
 * API. This list exists for one reason: the URL carries the track
 * (`/en/cka/lessons`), so middleware has to recognise a track segment and
 * `generateStaticParams` has to enumerate them, and both run where the backend
 * is unreachable (middleware on every request before any fetch, static params at
 * image build time).
 *
 * That makes it a duplicate of `backend/app/seed_data/tracks.json`, which is a
 * shape that has already bitten this project twice - a default written in two
 * places is really only written in the one that wins. `backend/tests/
 * test_track_config_sync.py` fails if the two lists drift apart.
 *
 * Deliberately only the slugs. Everything a user reads about a track comes from
 * `GET /tracks`, so adding a track to the API without touching this file gives
 * it working data and a missing route, rather than a half-translated ghost.
 */

export const TRACKS = [
  'cka',
  'cks',
  'lfcs',
  'aws',
  'comptia-a-plus',
  'comptia-linux-plus',
  'comptia-cysa-pentest',
  'docker',
  'python',
  'ansible',
  'cicd',
  'helm',
  'monitoring',
  'dbms',
  'terraform',
] as const;

export type TrackSlug = (typeof TRACKS)[number];

/** Where an unprefixed URL lands, and what the switcher starts on. */
export const DEFAULT_TRACK: TrackSlug = 'cka';

/**
 * Remembers the last track across visits. The URL stays the source of truth -
 * this only decides where "/en" sends somebody. Same relationship the locale
 * cookie has with the locale segment.
 */
export const TRACK_COOKIE = 'cka.track';

export function isTrack(value: string | undefined | null): value is TrackSlug {
  return !!value && (TRACKS as readonly string[]).includes(value);
}

export function normalizeTrack(value: string | undefined | null): TrackSlug {
  const base = value?.trim().toLowerCase();
  return isTrack(base) ? base : DEFAULT_TRACK;
}

/**
 * Builds an app path: ("/lessons", "uz", "docker") -> "/uz/docker/lessons".
 *
 * Some routes are deliberately outside the track segment - signing in, the
 * profile and the admin panel are not about one programme of study - so those
 * are passed through with the locale only.
 */
const TRACKLESS_PREFIXES = [
  '/login',
  '/auth',
  '/profile',
  '/admin',
  // Where you pick a track, so it cannot itself sit under one.
  '/tracks',
] as const;

/**
 * The sections that live inside a track.
 *
 * Named explicitly so middleware can tell an old bookmark from a typo:
 * `/en/lessons` is a pre-track URL and gets the current track prepended, while
 * `/en/nope/lessons` names a track that does not exist and must 404. Without
 * this distinction the second one becomes `/en/cka/nope/lessons`, which is
 * neither what was asked for nor an error.
 */
export const TRACK_SECTIONS = [
  'dashboard',
  'lessons',
  'roadmap',
  'labs',
  'quizzes',
  'resources',
] as const;

export function isTrackSection(value: string | undefined | null): boolean {
  return !!value && (TRACK_SECTIONS as readonly string[]).includes(value);
}

export function isTracklessPath(path: string): boolean {
  const clean = path.startsWith('/') ? path : `/${path}`;
  return TRACKLESS_PREFIXES.some(
    (prefix) => clean === prefix || clean.startsWith(`${prefix}/`),
  );
}

export function trackPath(path: string, locale: string, track: TrackSlug): string {
  const clean = path.startsWith('/') ? path : `/${path}`;
  if (isTracklessPath(clean)) {
    return clean === '/' ? `/${locale}` : `/${locale}${clean}`;
  }
  // A path that already names its track only needs the locale. The login
  // page's `next` is exactly such a path - the middleware keeps the track in
  // it so a sign-in returns to the right programme - and prepending the ACTIVE
  // track on top of it is how /uz/cka/cka/dashboard happened.
  if (isTrack(clean.split('/')[1])) {
    return `/${locale}${clean}`;
  }
  return clean === '/' ? `/${locale}/${track}` : `/${locale}/${track}${clean}`;
}

/** Strips a leading track segment: "/docker/lessons" -> "/lessons". */
export function stripTrack(pathname: string): string {
  const segments = pathname.split('/');
  if (isTrack(segments[1])) {
    const rest = segments.slice(2).join('/');
    return rest ? `/${rest}` : '/';
  }
  return pathname || '/';
}

/** Reads the track out of a full pathname, locale segment included or not. */
export function trackFromPathname(pathname: string): TrackSlug | null {
  const segments = pathname.split('/').filter(Boolean);
  for (const segment of segments.slice(0, 2)) {
    if (isTrack(segment)) return segment;
  }
  return null;
}
