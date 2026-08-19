'use client';

import { useEffect, useRef, useState } from 'react';

import { breakdown, clockFace, type Breakdown } from '@/components/countdown/breakdown';
import { ProgressRing } from '@/components/dashboard/progress-ring';
import { useI18n } from '@/i18n/provider';
import type { Enrollment } from '@/lib/types';
import { cn } from '@/lib/utils';

/**
 * How long is left, and whether that is good news.
 *
 * The server sends `server_now` with every enrollment. The offset between that
 * and the device clock is measured once and applied to every tick, so a machine
 * whose clock is a day out still sees the right number - otherwise the timer
 * would be wrong in exactly the situation where somebody is most likely to
 * blame the site.
 */
export function Countdown({
  enrollment,
  onRestart,
}: {
  enrollment: Enrollment;
  onRestart?: () => void;
}) {
  const { t, fill } = useI18n();
  const target = enrollment.target_date ? new Date(`${enrollment.target_date}T23:59:59`) : null;

  // Measured once per enrollment payload, not per render.
  const offsetRef = useRef(0);
  useEffect(() => {
    offsetRef.current = new Date(enrollment.server_now).getTime() - Date.now();
  }, [enrollment.server_now]);

  const compute = (): Breakdown | null =>
    target ? breakdown(new Date(Date.now() + offsetRef.current), target) : null;

  const [parts, setParts] = useState<Breakdown | null>(compute);

  useEffect(() => {
    if (!target) return;

    const tick = () => setParts(compute());
    tick();

    let timer = window.setInterval(tick, 1000);

    // A background tab is throttled to roughly once a minute, so the numbers
    // drift while it is hidden. Stopping and recomputing on return costs
    // nothing and means the timer is never visibly wrong at the moment somebody
    // looks at it.
    const onVisibility = () => {
      window.clearInterval(timer);
      if (document.visibilityState === 'visible') {
        tick();
        timer = window.setInterval(tick, 1000);
      }
    };

    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', onVisibility);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enrollment.target_date, enrollment.server_now]);

  if (!parts || !target) return null;

  const overdue = parts.overdue;
  const percent =
    enrollment.days_total > 0
      ? Math.round((enrollment.days_elapsed / enrollment.days_total) * 100)
      : 0;

  const units: Array<[number, string]> = [
    [parts.months, t.countdown.months],
    [parts.weeks, t.countdown.weeks],
    [parts.days, t.countdown.days],
    [parts.hours, t.countdown.hours],
  ];

  return (
    <section
      className={cn('cd-card', overdue && 'cd-card-overdue')}
      aria-live="off"
    >
      <div className="cd-main">
        <div className="flex items-baseline gap-2">
          {/* The state is a word, not only a colour - the red tint alone would
              be invisible to a colour-blind reader and meaningless out of
              context. */}
          <span className={cn('tech-label', overdue && 'cd-label-overdue')}>
            {overdue ? t.countdown.overdueLabel : t.countdown.remainingLabel}
          </span>
          <span className="cd-clock" aria-hidden>
            {clockFace(parts)}
          </span>
        </div>

        <ol className="cd-units">
          {units.map(([value, label]) => (
            <li key={label} className="cd-unit">
              <span className="cd-value tabular-nums">
                {String(value).padStart(2, '0')}
              </span>
              <span className="cd-unit-label">{label}</span>
            </li>
          ))}
        </ol>

        <p className="cd-target">
          {fill(overdue ? t.countdown.wasDue : t.countdown.dueOn, {
            date: enrollment.target_date ?? '',
          })}
          {enrollment.target_source === 'manual' && (
            <span className="cd-manual"> · {t.countdown.manualDate}</span>
          )}
        </p>

        {overdue && onRestart && (
          <button type="button" className="cd-restart" onClick={onRestart}>
            {t.countdown.restart}
          </button>
        )}
      </div>

      <div className="cd-ring">
        <ProgressRing
          value={percent}
          size={124}
          thickness={11}
          label={t.countdown.progressLabel}
          caption={fill(t.countdown.weekOf, {
            current: enrollment.expected_week,
            total: enrollment.duration_weeks,
          })}
        />
        {enrollment.behind_by_weeks > 0 && (
          <p className="cd-behind">
            {/* "1 weeks behind" reads as a bug in the code rather than a fact
                about the reader, so the singular has its own string - the same
                way the study streak already does it. */}
            {enrollment.behind_by_weeks === 1
              ? t.countdown.behindOne
              : fill(t.countdown.behind, { weeks: enrollment.behind_by_weeks })}
          </p>
        )}
      </div>
    </section>
  );
}
