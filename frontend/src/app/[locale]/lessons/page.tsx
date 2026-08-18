import type { Metadata } from 'next';
import Link from 'next/link';

import { CompletionProvider } from '@/components/completion';
import { LessonCard } from '@/components/lessons/lesson-card';
import type { LessonState } from '@/components/lessons/lesson-status';
import { PhaseProgress } from '@/components/lessons/phase-progress';
import { Card, CardContent } from '@/components/ui/card';
import { fill, getDictionary } from '@/i18n';
import { localePath, LOCALES, normalizeLocale } from '@/i18n/config';
import { serverFetch } from '@/lib/server-api';
import type { LessonSummary, PhaseDetail } from '@/lib/types';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const locale = normalizeLocale(params.locale);
  const t = getDictionary(locale);
  return {
    title: t.meta.lessonsTitle,
    description: t.meta.lessonsDescription,
    alternates: {
      canonical: `/${locale}/lessons`,
      languages: Object.fromEntries(LOCALES.map((l) => [l, `/${l}/lessons`])),
    },
  };
}

/** One lesson, flattened out of the phase -> week -> lesson tree. */
interface Row {
  lesson: LessonSummary;
  week: number;
  locked: boolean;
}

const byOrder = <T extends { order_index: number }>(items: T[]): T[] =>
  [...items].sort((a, b) => a.order_index - b.order_index);

export default async function LessonsPage({ params }: { params: { locale: string } }) {
  const locale = normalizeLocale(params.locale);
  const t = getDictionary(locale);
  const href = (path: string) => localePath(path, locale);

  const phases = (await serverFetch<PhaseDetail[]>('/roadmap', locale)) ?? [];

  /**
   * Curriculum order, phase by phase.
   *
   * Locked is taken straight from `phase.locked` - the API's own phase-unlock
   * gate, which is off unless the deployment enforces it. A draft lesson
   * (`is_placeholder`) is NOT locked: the page's own intro promises drafts you
   * can still navigate, so those stay open and are marked with a badge.
   */
  const groups = byOrder(phases).map((phase) => ({
    phase,
    rows: byOrder(phase.weeks).flatMap((week) =>
      byOrder(week.lessons).map<Row>((lesson) => ({
        lesson,
        week: week.number,
        locked: phase.locked,
      })),
    ),
  }));

  const rows = groups.flatMap((group) => group.rows);
  const totalLessons = rows.length;
  const doneLessons = rows.filter((row) => row.lesson.completed).length;
  const overallPercent = totalLessons ? Math.round((doneLessons / totalLessons) * 100) : 0;

  // Where the reader stands: the first lesson they can open and have not done.
  const currentSlug = rows.find((row) => !row.locked && !row.lesson.completed)?.lesson.slug;

  const stateOf = (row: Row): LessonState => {
    if (row.locked) return 'locked';
    if (row.lesson.completed) return 'done';
    return row.lesson.slug === currentSlug ? 'current' : 'todo';
  };

  return (
    <CompletionProvider>
      <div className="py-4">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div className="max-w-3xl">
            <h1 className="text-[28px] font-bold tracking-[-0.02em] text-ink">
              {t.lessons.heading}
            </h1>
            <p className="mt-2 text-ink-secondary">
              {fill(t.lessons.intro, { count: totalLessons })}
            </p>
          </div>
          {totalLessons > 0 && (
            <p className="font-mono text-xs tabular-nums text-ink-muted">
              {overallPercent}% · {doneLessons}/{totalLessons} {t.common.lessons}
            </p>
          )}
        </header>

        {groups.length === 0 ? (
          <Card className="mt-8">
            <CardContent className="pt-5 text-sm text-ink-muted">{t.lessons.empty}</CardContent>
          </Card>
        ) : (
          <div className="mt-9 flex flex-col gap-9">
            {groups.map(({ phase, rows: phaseRows }) => (
              <section key={phase.slug}>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
                  <span aria-hidden className="lsn-node">
                    {phase.order_index}
                  </span>
                  <h2 className="text-base font-semibold tracking-[-0.01em] text-ink">
                    <Link href={href(`/roadmap/${phase.slug}`)} className="hover:underline">
                      {phase.title}
                    </Link>
                  </h2>
                  <PhaseProgress
                    phase={phase.title}
                    slugs={phaseRows.map((row) => row.lesson.slug)}
                    fallbackDone={phaseRows.filter((row) => row.lesson.completed).length}
                  />
                </div>

                <ul className="lsn-grid mt-4">
                  {phaseRows.map((row) => (
                    <LessonCard
                      key={row.lesson.slug}
                      lesson={row.lesson}
                      week={row.week}
                      locale={locale}
                      state={stateOf(row)}
                    />
                  ))}
                </ul>
              </section>
            ))}
          </div>
        )}
      </div>
    </CompletionProvider>
  );
}
