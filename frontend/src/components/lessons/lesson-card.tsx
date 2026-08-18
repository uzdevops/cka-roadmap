import Link from 'next/link';

import { LessonStatus, type LessonState } from '@/components/lessons/lesson-status';
import { Badge } from '@/components/ui/badge';
import { fill, getDictionary } from '@/i18n';
import { localePath, type Locale } from '@/i18n/config';
import type { LessonSummary } from '@/lib/types';
import { cn, formatMinutes } from '@/lib/utils';

/**
 * One lesson in the grid. The whole card is the link, so the hit target is the
 * card rather than the title.
 *
 * A locked card still links: the phase lock is enforced on quizzes, not on
 * lessons, and the roadmap page links the same lesson unconditionally. The
 * padlock and the reason line carry the state instead.
 */
export function LessonCard({
  lesson,
  week,
  locale,
  state,
}: {
  lesson: LessonSummary;
  week: number;
  locale: Locale;
  state: LessonState;
}) {
  const t = getDictionary(locale);
  const locked = state === 'locked';

  // Week and estimate. A quiz score would belong here too, but the list this
  // page is built from (`/roadmap` -> LessonSummary) carries no quiz fields, so
  // the segment is left out rather than faked.
  const meta = [
    fill(t.dashboard.weekShort, { number: week }),
    formatMinutes(lesson.estimated_minutes, t.common.minutes),
  ].join(' · ');

  const body = (
    <>
      <LessonStatus slug={lesson.slug} completed={lesson.completed} state={state} />

      <span className="min-w-0 flex-1">
        <span className="block text-[15px] font-semibold leading-snug text-ink">
          {lesson.title}
        </span>
        <span className="tech-label mt-1.5 block">{meta}</span>
        {locked && (
          <span className="mt-1.5 block text-[11px] leading-snug text-ink-muted">
            {t.quizzes.locked}
          </span>
        )}
      </span>

      {lesson.is_placeholder && (
        <Badge variant="outline" className="shrink-0">
          {t.common.draft}
        </Badge>
      )}
    </>
  );

  return (
    <li>
      <Link
        href={localePath(`/lessons/${lesson.slug}`, locale)}
        className={cn(
          'lsn-card card-hover',
          state === 'current' && 'lsn-card-current',
          locked && 'lsn-card-locked',
        )}
      >
        {body}
      </Link>
    </li>
  );
}
