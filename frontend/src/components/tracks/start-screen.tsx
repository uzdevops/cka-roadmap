'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

import { ConnectPanel } from '@/components/telegram/connect-panel';
import { Button } from '@/components/ui/button';
import { useI18n } from '@/i18n/provider';
import { startTrack } from '@/lib/tracks-api';
import type { Enrollment, Track } from '@/lib/types';

/**
 * What stands between somebody and a track they have not opened.
 *
 * The point of the button is the date: a roadmap measured in weeks is
 * meaningless without a day one to count them from, so nothing behind this
 * screen has a deadline until it is pressed.
 *
 * It states what is being committed to first - how long, how much - because
 * "twenty weeks" is a real thing to ask of a person and they should see it
 * before they agree to it.
 */
export function StartScreen({
  enrollment,
  track,
  onStarted,
}: {
  enrollment: Enrollment;
  track?: Track | null;
  onStarted?: (next: Enrollment) => void;
}) {
  const { t, fill } = useI18n();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async () => {
    setBusy(true);
    setError(null);
    try {
      const next = await startTrack(enrollment.track_slug);
      onStarted?.(next);
      // The gate lives in a server layout, so the new enrollment only takes
      // effect once the server renders again.
      router.refresh();
    } catch {
      setError(t.start.failed);
      setBusy(false);
    }
  };

  const facts: Array<[number, string]> = [
    [enrollment.duration_weeks, t.start.weeks],
    [enrollment.total_lessons, t.start.lessons],
    [enrollment.total_labs, t.start.labs],
    [enrollment.total_quizzes, t.start.quizzes],
  ];

  return (
    <div className="start-wrap">
      <section className="start-card">
        <span className="tech-label">{t.start.eyebrow}</span>

        <h1 className="start-title">{track?.title ?? enrollment.track_slug}</h1>
        {track?.summary && <p className="start-summary">{track.summary}</p>}

        <ol className="start-facts">
          {facts.map(([value, label]) => (
            <li key={label} className="start-fact">
              <span className="start-fact-value tabular-nums">{value}</span>
              <span className="start-fact-label">{label}</span>
            </li>
          ))}
        </ol>

        {enrollment.projected_target_date && (
          <p className="start-projection">
            {fill(t.start.projection, {
              date: enrollment.projected_target_date,
            })}
          </p>
        )}

        <Button
          size="lg"
          className="mt-6 w-full"
          onClick={start}
          disabled={busy}
        >
          {busy ? t.start.starting : t.start.button}
        </Button>

        {error && (
          <p role="alert" className="mt-3 text-sm text-[var(--critical)]">
            {error}
          </p>
        )}

        <p className="start-note">{t.start.note}</p>

        {/* Offered at the moment somebody commits to a schedule, which is when
            a daily nudge is worth having. Renders nothing when no bot is
            configured, and skipping it costs nothing - the panel is on the
            profile page permanently. */}
        <div className="start-telegram">
          <ConnectPanel compact />
        </div>
      </section>
    </div>
  );
}
