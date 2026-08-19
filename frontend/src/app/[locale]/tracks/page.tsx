'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Card } from '@/components/ui/card';
import { Meter } from '@/components/ui/meter';
import { useI18n } from '@/i18n/provider';
import { listTracks } from '@/lib/tracks-api';
import type { Track } from '@/lib/types';
import { cn } from '@/lib/utils';

/**
 * Every programme this account can open, and where it stands in each.
 *
 * Outside the [track] segment on purpose: this is the page you use to CHOOSE a
 * track, so it cannot itself live under one.
 */
export default function TracksPage() {
  const { t, fill, locale } = useI18n();
  const [tracks, setTracks] = useState<Track[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    listTracks(controller.signal)
      .then(setTracks)
      .catch(() => setFailed(true));
    return () => controller.abort();
  }, []);

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

      {failed && <p className="mt-8 text-sm text-[var(--critical)]">{t.tracks.failed}</p>}
      {tracks === null && !failed && (
        <p className="mt-8 text-sm text-ink-muted">{t.common.loading}</p>
      )}

      {tracks?.map === undefined
        ? null
        : groups.map(([title, belongs]) => {
            const members = tracks.filter(belongs);
            if (members.length === 0) return null;
            return (
              <section key={title} className="mt-10">
                <h2 className="text-xl font-semibold tracking-tight text-ink">{title}</h2>
                <ul className="trk-grid mt-5">
                  {members.map((entry) => {
                    const e = entry.enrollment;
                    const started = e && e.status !== 'not_started';
                    const percent =
                      started && e.duration_weeks
                        ? Math.min(
                            100,
                            Math.round(((e.current_week ?? 0) / e.duration_weeks) * 100),
                          )
                        : 0;

                    return (
                      <li key={entry.slug}>
                        <Card className="trk-card card-hover">
                          <div className="flex items-start gap-3">
                            <span aria-hidden className="trk-card-mark">
                              {entry.mark || entry.short_title.slice(0, 2).toUpperCase()}
                            </span>
                            <div className="min-w-0">
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
                          </div>

                          {entry.summary && (
                            <p className="trk-card-summary">{entry.summary}</p>
                          )}

                          {started ? (
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
                          ) : (
                            <p className="trk-card-idle">
                              {fill(t.tracks.durationWeeks, {
                                weeks: e?.duration_weeks ?? 0,
                              })}
                            </p>
                          )}

                          <Link
                            href={`/${locale}/${entry.slug}/dashboard`}
                            className={cn('trk-card-cta', !started && 'trk-card-cta-start')}
                          >
                            {started ? t.tracks.continue : t.tracks.start}
                          </Link>
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
