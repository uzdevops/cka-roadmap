'use client';

import { useState } from 'react';

import { useI18n } from '@/i18n/provider';
import type { PhaseProgress } from '@/lib/types';
import { cn } from '@/lib/utils';

/**
 * Lesson completion per phase.
 *
 * One measure across six categories, so it is ONE series in ONE colour - the
 * categories are named on the axis, not encoded as hue. Bars grow from a single
 * baseline, are capped thin, and carry a 4px rounded data-end that stays square
 * where it meets the baseline. Values are direct-labelled at the tip; the
 * tooltip carries the detail.
 */
export function PhaseProgressChart({ phases }: { phases: PhaseProgress[] }) {
  const { t, fill } = useI18n();
  const [view, setView] = useState<'chart' | 'table'>('chart');
  const [hovered, setHovered] = useState<string | null>(null);

  if (phases.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-ink-muted">{t.dashboard.phaseChartEmpty}</p>
    );
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="text-sm text-ink-secondary">{t.dashboard.phaseChartCaption}</p>
        <ViewToggle view={view} onChange={setView} />
      </div>

      {view === 'table' ? (
        <ProgressTable phases={phases} />
      ) : (
        <ul className="flex flex-col gap-3">
          {phases.map((phase) => {
            const percent = Math.max(0, Math.min(100, phase.progress_percent));
            const active = hovered === phase.phase_slug;
            return (
              <li
                key={phase.phase_slug}
                className="relative"
                onMouseEnter={() => setHovered(phase.phase_slug)}
                onMouseLeave={() => setHovered(null)}
                onFocus={() => setHovered(phase.phase_slug)}
                onBlur={() => setHovered(null)}
                tabIndex={0}
              >
                <div className="mb-1.5 flex items-baseline justify-between gap-3">
                  <span className="truncate text-sm text-ink">{phase.phase_title}</span>
                  <span className="shrink-0 text-sm font-semibold tabular-nums text-ink">
                    {percent.toFixed(0)}%
                  </span>
                </div>

                {/* Track is a step of the fill's own ramp, close to the surface,
                    so an empty bar can never be misread as a full one. */}
                <div
                  className="h-2.5 w-full overflow-hidden rounded-full"
                  style={{ background: 'var(--track)' }}
                  role="img"
                  aria-label={fill(t.dashboard.phaseBarAria, {
                    phase: phase.phase_title,
                    done: phase.completed_lessons,
                    total: phase.total_lessons,
                  })}
                >
                  <div
                    className="h-full transition-[width] duration-500"
                    style={{
                      width: `${percent}%`,
                      background: 'var(--accent)',
                      borderRadius: '0 4px 4px 0',
                    }}
                  />
                </div>

                {active && (
                  <div className="pointer-events-none absolute -top-1 right-0 z-10 -translate-y-full rounded-lg border border-line bg-surface px-3 py-2 text-xs shadow-lg">
                    <p className="font-semibold text-ink">{phase.phase_title}</p>
                    <p className="mt-1 text-ink-secondary">
                      {phase.completed_lessons} / {phase.total_lessons} {t.common.lessons}
                    </p>
                    <p className="text-ink-secondary">
                      {t.dashboard.colQuizAvg}:{' '}
                      {phase.quiz_average === null
                        ? t.dashboard.notAttempted
                        : `${phase.quiz_average}%`}
                    </p>
                    {phase.exam_weight > 0 && (
                      <p className="text-ink-muted">
                        {t.dashboard.colWeight} {phase.exam_weight}%
                      </p>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

function ProgressTable({ phases }: { phases: PhaseProgress[] }) {
  const { t } = useI18n();
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-axis text-left text-xs uppercase tracking-wide text-ink-muted">
            <th className="py-2 pr-3 font-medium">{t.dashboard.colPhase}</th>
            <th className="py-2 pr-3 text-right font-medium">{t.dashboard.colLessons}</th>
            <th className="py-2 pr-3 text-right font-medium">{t.dashboard.colProgress}</th>
            <th className="py-2 text-right font-medium">{t.dashboard.colQuizAvg}</th>
          </tr>
        </thead>
        <tbody>
          {phases.map((phase) => (
            <tr key={phase.phase_slug} className="border-b border-line">
              <td className="py-2 pr-3 text-ink">{phase.phase_title}</td>
              <td className="py-2 pr-3 text-right tabular-nums text-ink-secondary">
                {phase.completed_lessons} / {phase.total_lessons}
              </td>
              <td className="py-2 pr-3 text-right tabular-nums text-ink-secondary">
                {phase.progress_percent.toFixed(0)}%
              </td>
              <td className="py-2 text-right tabular-nums text-ink-secondary">
                {phase.quiz_average === null ? '-' : `${phase.quiz_average}%`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ViewToggle({
  view,
  onChange,
}: {
  view: 'chart' | 'table';
  onChange: (view: 'chart' | 'table') => void;
}) {
  const { t } = useI18n();
  const labels = { chart: t.common.chart, table: t.common.table };
  return (
    <div className="flex shrink-0 rounded-lg border border-line p-0.5" role="group">
      {(['chart', 'table'] as const).map((value) => (
        <button
          key={value}
          type="button"
          onClick={() => onChange(value)}
          aria-pressed={view === value}
          className={cn(
            'rounded-md px-2.5 py-1 text-xs font-medium capitalize transition-colors',
            view === value
              ? 'bg-[var(--surface-2)] text-ink'
              : 'text-ink-muted hover:text-ink-secondary',
          )}
        >
          {labels[value]}
        </button>
      ))}
    </div>
  );
}
