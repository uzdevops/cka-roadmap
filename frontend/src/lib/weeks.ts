import type { LessonSummary, PhaseDetail } from '@/lib/types';

export type WeekState = 'complete' | 'active' | 'pending';

export interface WeekRow {
  number: number;
  title: string;
  phaseSlug: string;
  phaseTitle: string;
  /** Phase `order_index`, which drives both the identity colour and the glyph. */
  phaseIndex: number;
  lessons: LessonSummary[];
  done: number;
  total: number;
  percent: number;
  state: WeekState;
}

/**
 * Flattens the roadmap into the twenty week rows the dashboard renders, and
 * marks exactly one of them `active`: the earliest week that is not finished.
 *
 * Counts come from the lessons themselves rather than the week's own totals, so
 * the meter can never disagree with the checklist printed underneath it.
 */
export function buildWeeks(phases: PhaseDetail[]): WeekRow[] {
  const rows: WeekRow[] = [];

  for (const phase of phases) {
    for (const week of phase.weeks) {
      const total = week.lessons.length;
      const done = week.lessons.filter((lesson) => lesson.completed).length;

      rows.push({
        number: week.number,
        title: week.title,
        phaseSlug: phase.slug,
        phaseTitle: phase.title,
        phaseIndex: phase.order_index,
        lessons: week.lessons,
        done,
        total,
        percent: total === 0 ? 0 : Math.round((done / total) * 100),
        state: total > 0 && done === total ? 'complete' : 'pending',
      });
    }
  }

  rows.sort((a, b) => a.number - b.number);

  const next = rows.find((row) => row.state !== 'complete');
  if (next) next.state = 'active';

  return rows;
}

export interface WeekTally {
  complete: number;
  active: number;
  pending: number;
  total: number;
}

export function tallyWeeks(rows: WeekRow[]): WeekTally {
  return {
    complete: rows.filter((r) => r.state === 'complete').length,
    active: rows.filter((r) => r.state === 'active').length,
    pending: rows.filter((r) => r.state === 'pending').length,
    total: rows.length,
  };
}
