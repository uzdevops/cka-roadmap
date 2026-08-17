'use client';

import Link from 'next/link';

import { PhaseGlyph } from '@/components/dashboard/phase-glyph';
import { useI18n } from '@/i18n/provider';
import type { WeekRow, WeekState } from '@/lib/weeks';
import { cn, phaseColor } from '@/lib/utils';

/**
 * Twenty weeks at a glance, then twenty cards.
 *
 * State is never carried by colour alone: every segment and card also states
 * its week number and its "3 / 3" count, and each card names its state in text.
 */

function stateLabel(state: WeekState, t: ReturnType<typeof useI18n>['t']): string {
  if (state === 'complete') return t.dashboard.weekComplete;
  if (state === 'active') return t.dashboard.weekActive;
  return t.dashboard.weekPending;
}

/** The horizontal twenty-segment bar above the grid. */
export function WeekStatusBar({ weeks }: { weeks: WeekRow[] }) {
  const { t, fill } = useI18n();

  return (
    <ol className="flex w-full gap-1" aria-label={t.dashboard.weekBarLabel}>
      {weeks.map((week) => (
        <li key={week.number} className="min-w-0 flex-1">
          <span
            className={cn('dash-seg', `dash-seg-${week.state}`)}
            title={`${fill(t.lessons.week, { number: week.number })} — ${stateLabel(
              week.state,
              t,
            )} (${week.done}/${week.total})`}
          >
            <span className="sr-only">
              {fill(t.lessons.week, { number: week.number })}: {stateLabel(week.state, t)}
            </span>
          </span>
        </li>
      ))}
    </ol>
  );
}

function WeekCard({ week }: { week: WeekRow }) {
  const { t, href, fill } = useI18n();
  const tint = phaseColor(week.phaseIndex);

  return (
    <li>
      <article
        className={cn('dash-week', `dash-week-${week.state}`)}
        style={{ '--week-tint': tint } as React.CSSProperties}
      >
        <div className="flex items-center gap-2">
          <span className="dash-week-badge">
            <PhaseGlyph index={week.phaseIndex} size={14} />
            <span>{fill(t.dashboard.weekShort, { number: week.number })}</span>
          </span>
          <span className="ml-auto shrink-0 text-[11px] font-medium uppercase tracking-wide text-ink-muted">
            {stateLabel(week.state, t)}
          </span>
        </div>

        <Link
          href={href(`/roadmap/${week.phaseSlug}`)}
          className="mt-2 block text-sm font-semibold leading-snug text-ink hover:text-[var(--accent)]"
        >
          {week.title}
        </Link>

        <div className="mt-3 flex items-center gap-2">
          <span
            className="dash-week-track"
            role="meter"
            aria-valuenow={week.percent}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={fill(t.dashboard.weekMeterLabel, { number: week.number })}
          >
            <span className="dash-week-fill" style={{ width: `${week.percent}%` }} />
          </span>
          <span className="shrink-0 text-xs tabular-nums text-ink-muted">
            {week.done}/{week.total}
          </span>
        </div>

        <ul className="mt-3 flex flex-col gap-1.5">
          {week.lessons.map((lesson) => (
            <li key={lesson.slug} className="flex items-start gap-2">
              <span
                aria-hidden
                className={cn('dash-check', lesson.completed && 'dash-check-on')}
              >
                {lesson.completed ? '✓' : ''}
              </span>
              <Link
                href={href(`/lessons/${lesson.slug}`)}
                // The tick already says "done"; striking the title through as
                // well only makes it harder to read at 12px.
                className={cn(
                  'min-w-0 text-xs leading-snug hover:text-[var(--accent)]',
                  lesson.completed ? 'text-ink-muted' : 'text-ink-secondary',
                )}
              >
                {lesson.title}
              </Link>
            </li>
          ))}
        </ul>
      </article>
    </li>
  );
}

export function WeekGrid({ weeks }: { weeks: WeekRow[] }) {
  return (
    <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {weeks.map((week) => (
        <WeekCard key={week.number} week={week} />
      ))}
    </ul>
  );
}
