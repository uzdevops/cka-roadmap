import { cookies } from 'next/headers';

import { DEFAULT_LOCALE, type Locale } from '@/i18n/config';
import { ACCESS_COOKIE, serverApiUrl } from '@/lib/api';
import { DEFAULT_TRACK, type TrackSlug } from '@/tracks/config';

const API_V1 = '/api/v1';

/**
 * Server-side fetching for the pages that render on the server.
 *
 * The API refuses anonymous callers now, so this forwards the visitor's access
 * token out of the request cookies. It lives in its own module because
 * `next/headers` is server-only and `lib/api` is imported by client components.
 */
export async function serverFetch<T>(
  path: string,
  locale: Locale = DEFAULT_LOCALE,
  track: TrackSlug = DEFAULT_TRACK,
): Promise<T | null> {
  const separator = path.includes('?') ? '&' : '?';
  const url =
    `${serverApiUrl()}${API_V1}${path}${separator}lang=${locale}&track=${track}`;

  const token = cookies().get(ACCESS_COOKIE)?.value;

  try {
    // Always live: the backend is not reachable during the image build, so a
    // prerendered page would bake in an empty state permanently. Pages using
    // this also set `export const dynamic = 'force-dynamic'`.
    const res = await fetch(url, {
      headers: {
        Accept: 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      cache: 'no-store',
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    // The backend may be briefly unavailable during a restart; pages that use
    // this render an empty state rather than a 500.
    return null;
  }
}
