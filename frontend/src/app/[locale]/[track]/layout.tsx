import { notFound } from 'next/navigation';

import { StartScreen } from '@/components/tracks/start-screen';
import { normalizeLocale } from '@/i18n/config';
import { I18nProvider } from '@/i18n/provider';
import { serverFetch } from '@/lib/server-api';
import type { Enrollment, Track } from '@/lib/types';
import { TRACKS, isTrack } from '@/tracks/config';

/**
 * Everything under a track: the roadmap, lessons, labs, quizzes, resources and
 * the dashboard. Signing in, the profile and the admin panel deliberately sit
 * outside it - none of them is about one programme of study.
 *
 * This is also where the Start gate lives. Putting it in the layout rather than
 * in each page means a track that has not been started cannot be reached by
 * deep link either, and there is exactly one place that decides it.
 */

// The gate depends on who is asking, so nothing under here can be prerendered.
export const dynamic = 'force-dynamic';

export function generateStaticParams() {
  // A hardcoded list rather than a fetch: this runs at image build time, when
  // the backend is not reachable. `backend/tests/test_track_config_sync.py`
  // keeps it in step with seed_data/tracks.json.
  return TRACKS.map((track) => ({ track }));
}

export default async function TrackLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { locale: string; track: string };
}) {
  // A static sibling segment beats [track] in Next's matcher, so /en/login
  // never reaches here - but an invented slug like /en/nope/lessons would, and
  // it has to 404 rather than render an empty roadmap.
  if (!isTrack(params.track)) notFound();

  const locale = normalizeLocale(params.locale);
  const enrollment = await serverFetch<Enrollment>(
    `/tracks/${params.track}/enrollment`,
    locale,
    params.track,
  );

  // Nested inside the locale layout's provider, which mounts without a track
  // because it sits above this segment. Re-mounting here means `href()` and the
  // API client both carry the track the URL actually names.
  const body =
    enrollment?.status === 'not_started' ? (
      <StartScreen
        enrollment={enrollment}
        track={
          (await serverFetch<Track[]>('/tracks', locale, params.track))?.find(
            (entry) => entry.slug === params.track,
          ) ?? null
        }
      />
    ) : (
      children
    );

  return (
    <I18nProvider locale={locale} track={params.track}>
      {body}
    </I18nProvider>
  );
}
