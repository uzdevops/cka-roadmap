import { notFound } from 'next/navigation';

import { normalizeLocale } from '@/i18n/config';
import { I18nProvider } from '@/i18n/provider';
import { TRACKS, isTrack } from '@/tracks/config';

/**
 * Everything under a track: the roadmap, lessons, labs, quizzes, resources and
 * the dashboard. Signing in, the profile and the admin panel deliberately sit
 * outside it - none of them is about one programme of study.
 *
 * This is a fragment wrapper. `<html>` and the app shell belong to the locale
 * layout above; all this adds is the track.
 */

export function generateStaticParams() {
  // A hardcoded list rather than a fetch: this runs at image build time, when
  // the backend is not reachable. `backend/tests/test_track_config_sync.py`
  // keeps it in step with seed_data/tracks.json.
  return TRACKS.map((track) => ({ track }));
}

export default function TrackLayout({
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

  // Nested inside the locale layout's provider, which mounts with the default
  // track because it sits above this segment and cannot know better. Re-mounting
  // here overrides the context, so `href()` and the API client both carry the
  // track the URL actually names.
  return (
    <I18nProvider locale={normalizeLocale(params.locale)} track={params.track}>
      {children}
    </I18nProvider>
  );
}
