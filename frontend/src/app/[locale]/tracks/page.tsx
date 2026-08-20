'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { buttonVariants } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Meter } from '@/components/ui/meter';
import { useI18n } from '@/i18n/provider';
import { listTracks } from '@/lib/tracks-api';
import type { Track } from '@/lib/types';
import { cn } from '@/lib/utils';

/**
 * Every programme this account can open, and where it stands in each - the
 * primary way a track is picked, so each card answers the questions somebody
 * choosing one actually has: what is it, how big is it, have I started it.
 *
 * Outside the [track] segment on purpose: this is the page you use to CHOOSE a
 * track, so it cannot itself live under one. The cards only navigate - the
 * commitment (the Start button, the date) lives on the track's own Start
 * screen, where it can say what it is asking of you.
 */

type Filter = 'all' | 'active' | 'not_started';

const isStarted = (entry: Track) =>
  entry.enrollment != null && entry.enrollment.status !== 'not_started';

/** Where pressing Start today would put the finish line - the same sum the
    Start screen shows, so the card and the screen never disagree. */
function projectedFinish(weeks: number): string {
  const date = new Date();
  date.setDate(date.getDate() + weeks * 7);
  return date.toISOString().slice(0, 10);
}

export default function TracksPage() {
  const { t, fill, locale } = useI18n();
  const [tracks, setTracks] = useState<Track[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [filter, setFilter] = useState<Filter>('all');

  useEffect(() => {
    const controller = new AbortController();
    listTracks(controller.signal)
      .then(setTracks)
      .catch(() => setFailed(true));
    return () => controller.abort();
  }, []);

  const filters: Array<[Filter, string]> = [
    ['all', t.tracks.filterAll],
    ['active', t.tracks.filterActive],
    ['not_started', t.tracks.filterNotStarted],
  ];

  const matchesFilter = (entry: Track) =>
    filter === 'all' || (filter === 'active') === isStarted(entry);

  const groups: Array<[string, (entry: Track) => boolean]> = [
    [t.tracks.certificates, (entry) => entry.is_certificate],
    // A track that is both appears in both groups - that is the point of two
    // flags rather than one type, and hiding it from one list would misrepresent
    // what it is.
    [t.tracks.topics, (entry) => entry.is_topic],
  ];

  return (
    <div className="py-4">
      <header className="max-w-3xl">
        <h1 className="text-[28px] font-bold tracking-[-0.02em] text-ink">
          {t.tracks.heading}
        </h1>
        <p className="mt-2 text-ink-secondary">{t.tracks.intro}</p>
      </header>

      {tracks !== null && tracks.length > 0 && (
        <div className="trk-filters mt-6" role="group" aria-label={t.tracks.heading}>
          {filters.map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => setFilter(value)}
              aria-pressed={filter === value}
              className={cn('trk-filter', filter === value && 'trk-filter-active')}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {failed && <p className="mt-8 text-sm text-[var(--critical)]">{t.tracks.failed}</p>}
      {tracks === null && !failed && (
        <p className="mt-8 text-sm text-ink-muted">{t.common.loading}</p>
      )}

      {tracks?.map === undefined
        ? null
        : groups.map(([title, belongs]) => {
            const members = tracks.filter((entry) => belongs(entry) && matchesFilter(entry));
            if (members.length === 0) return null;
            return (
              <section key={title} className="mt-10">
                <h2 className="text-xl font-semibold tracking-tight text-ink">{title}</h2>
                <ul className="trk-grid mt-5">
                  {members.map((entry) => {
                    const e = entry.enrollment;
                    const started = isStarted(entry);
                    const percent =
                      started && e && e.duration_weeks
                        ? Math.min(
                            100,
                            Math.round(((e.current_week ?? 0) / e.duration_weeks) * 100),
                          )
                        : 0;

                    const stats: Array<[string, number]> = [
                      [t.tracks.statWeeks, e?.duration_weeks ?? 0],
                      [t.tracks.statLessons, e?.total_lessons ?? 0],
                      [t.tracks.statLabs, e?.total_labs ?? 0],
                      [t.tracks.statQuizzes, e?.total_quizzes ?? 0],
                    ];

                    return (
                      <li key={entry.slug}>
                        <Card
                          className={cn(
                            'trk-card card-hover',
                            started && 'trk-card-active',
                          )}
                        >
                          <div className="flex items-start gap-3">
                            {/* Tinted from the track's OWN accent, so a wall of
                                fifteen cards reads as fifteen subjects rather
                                than one brand repeated. The colour is data. */}
                            <span
                              aria-hidden
                              className="trk-card-mark trk-card-mark-tinted"
                              style={
                                entry.accent
                                  ? {
                                      background: `color-mix(in srgb, ${entry.accent} 14%, transparent)`,
                                      borderColor: `color-mix(in srgb, ${entry.accent} 35%, transparent)`,
                                      color: entry.accent,
                                    }
                                  : undefined
                              }
                            >
                              {entry.mark || entry.short_title.slice(0, 2).toUpperCase()}
                            </span>
                            <div className="min-w-0 flex-1">
                              <h3 className="trk-card-name">{entry.title}</h3>
                              <p className="trk-card-kind">
                                {[
                                  entry.is_topic ? t.tracks.topic : null,
                                  entry.is_certificate ? t.tracks.certificate : null,
                                  entry.exam_code,
                                ]
                                  .filter(Boolean)
                                  .join(' · ')}
                              </p>
                            </div>
                            <Badge variant={started ? 'good' : 'neutral'}>
                              {e?.status === 'completed'
                                ? t.tracks.done
                                : started
                                  ? t.tracks.filterActive
                                  : t.tracks.filterNotStarted}
                            </Badge>
                          </div>

                          {entry.summary && (
                            <p className="trk-card-summary truncate">{entry.summary}</p>
                          )}

                          {/* How big a thing this is, before anyone commits to
                              it - the numbers come with the list, not from a
                              request per card. */}
                          <dl className="trk-stats">
                            {stats.map(([label, value]) => (
                              <div key={label} className="trk-stat">
                                <dd className="trk-stat-value">{value}</dd>
                                <dt className="trk-stat-label">{label}</dt>
                              </div>
                            ))}
                          </dl>

                          {!started && (e?.duration_weeks ?? 0) > 0 && (
                            <p className="trk-card-projection">
                              {fill(t.start.projection, {
                                date: projectedFinish(e!.duration_weeks),
                              })}
                            </p>
                          )}

                          {started && e && (
                            <div className="mt-4">
                              <Meter
                                value={percent}
                                label={fill(t.tracks.weekOf, {
                                  current: e.current_week ?? 1,
                                  total: e.duration_weeks,
                                })}
                              />
                              {e.is_overdue && (
                                <p className="trk-card-late">{t.tracks.overdue}</p>
                              )}
                            </div>
                          )}

                          {/* A real button, full width, because this is the
                              one action on the card - but it only navigates:
                              the clock starts on the track's own Start screen. */}
                          <div className="mt-auto pt-5">
                            <Link
                              href={`/${locale}/${entry.slug}/dashboard`}
                              className={cn(buttonVariants({ size: 'lg' }), 'w-full')}
                            >
                              {started ? t.tracks.continue : t.tracks.start}
                            </Link>
                          </div>
                        </Card>
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })}
    </div>
  );
}
