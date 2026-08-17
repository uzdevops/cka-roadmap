import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { CompletionDot, CompletionProvider, WeekProgress } from '@/components/completion';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { fill, getDictionary } from '@/i18n';
import { localePath, LOCALES, normalizeLocale } from '@/i18n/config';
import { serverFetch } from '@/lib/server-api';
import type { PhaseDetail } from '@/lib/types';
import { formatMinutes, phaseColor } from '@/lib/utils';

export const dynamic = 'force-dynamic';

const DAY_KEYS = ['', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const;

const DAY_LABELS: Record<string, Record<string, string>> = {
  en: { mon: 'Mon', tue: 'Tue', wed: 'Wed', thu: 'Thu', fri: 'Fri', sat: 'Sat', sun: 'Sun' },
  uz: { mon: 'Du', tue: 'Se', wed: 'Ch', thu: 'Pa', fri: 'Ju', sat: 'Sh', sun: 'Ya' },
};

export async function generateMetadata({
  params,
}: {
  params: { locale: string; slug: string };
}): Promise<Metadata> {
  const locale = normalizeLocale(params.locale);
  const phase = await serverFetch<PhaseDetail>(`/roadmap/phases/${params.slug}`, locale);
  if (!phase) return { title: 'Not found' };

  return {
    title: phase.title,
    description: phase.description.slice(0, 300),
    alternates: {
      canonical: `/${locale}/roadmap/${phase.slug}`,
      languages: Object.fromEntries(
        LOCALES.map((l) => [l, `/${l}/roadmap/${phase.slug}`]),
      ),
    },
    openGraph: { title: phase.title, description: phase.description.slice(0, 300) },
  };
}

export default async function PhasePage({
  params,
}: {
  params: { locale: string; slug: string };
}) {
  const locale = normalizeLocale(params.locale);
  const t = getDictionary(locale);
  const href = (path: string) => localePath(path, locale);
  const days = DAY_LABELS[locale] ?? DAY_LABELS.en;

  const phase = await serverFetch<PhaseDetail>(`/roadmap/phases/${params.slug}`, locale);
  if (!phase) notFound();

  return (
    <CompletionProvider>
      <div className="py-4">
        <Link href={href('/roadmap')} className="text-sm text-ink-muted hover:text-ink">
          {t.roadmap.allPhases}
        </Link>

        <header className="mt-4 max-w-3xl">
          <div className="flex items-center gap-2">
            <span
              aria-hidden
              className="h-3 w-3 rounded-full"
              style={{ background: phaseColor(phase.order_index) }}
            />
            <span className="text-xs font-medium uppercase tracking-wide text-ink-muted">
              {fill(t.home.weeksRange, { start: phase.week_start, end: phase.week_end })}
            </span>
            {phase.exam_weight > 0 && (
              <Badge variant="accent">
                {fill(t.home.examWeight, { weight: phase.exam_weight })}
              </Badge>
            )}
          </div>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-ink">{phase.title}</h1>
          <p className="mt-3 text-ink-secondary">{phase.description}</p>
          {phase.exam_domain && (
            <p className="mt-2 text-sm text-ink-muted">
              {fill(t.roadmap.examDomain, { domain: phase.exam_domain })}
            </p>
          )}
        </header>

        <section className="mt-10">
          <h2 className="text-lg font-semibold tracking-tight text-ink">
            {t.roadmap.weeklySchedule}
          </h2>
          <div className="mt-4 flex flex-col gap-4">
            {phase.weeks.map((week) => (
              <Card key={week.id}>
                <CardContent className="pt-5">
                  <div className="flex items-baseline justify-between gap-3">
                    <h3 className="font-semibold text-ink">{week.title}</h3>
                    <WeekProgress slugs={week.lessons.map((l) => l.slug)} />
                  </div>
                  {week.description && (
                    <p className="mt-1.5 text-sm text-ink-secondary">{week.description}</p>
                  )}

                  <ul className="mt-4 flex flex-col divide-y divide-[var(--border)]">
                    {week.lessons.map((lesson) => (
                      <li key={lesson.slug}>
                        <Link
                          href={href(`/lessons/${lesson.slug}`)}
                          className="flex items-center gap-3 py-2.5 transition-colors hover:text-ink"
                        >
                          <CompletionDot slug={lesson.slug} />
                          <span className="w-9 shrink-0 text-xs text-ink-muted">
                            {lesson.day_of_week ? days[DAY_KEYS[lesson.day_of_week]] : ''}
                          </span>
                          <span className="flex-1 text-sm text-ink-secondary">
                            {lesson.title}
                          </span>
                          {lesson.is_placeholder && (
                            <Badge variant="outline" className="shrink-0">
                              {t.common.draft}
                            </Badge>
                          )}
                          <span className="shrink-0 text-xs tabular-nums text-ink-muted">
                            {formatMinutes(lesson.estimated_minutes, t.common.minutes)}
                          </span>
                        </Link>
                      </li>
                    ))}
                  </ul>

                  <p className="mt-4 border-t border-line pt-3 text-xs text-ink-muted">
                    {t.roadmap.weekendNote}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {phase.quizzes.length > 0 && (
          <section className="mt-10">
            <h2 className="text-lg font-semibold tracking-tight text-ink">
              {t.roadmap.quizzesHeading}
            </h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {phase.quizzes.map((quiz) => (
                <Link key={quiz.slug} href={href(`/quizzes/${quiz.slug}`)} className="group">
                  <Card className="h-full transition-colors group-hover:border-[var(--accent)]">
                    <CardContent className="pt-5">
                      <h3 className="font-semibold text-ink">{quiz.title}</h3>
                      <p className="mt-1.5 text-sm text-ink-secondary">{quiz.description}</p>
                      <p className="mt-3 text-xs text-ink-muted">
                        {quiz.time_limit_minutes
                          ? fill(t.roadmap.quizMetaTimed, {
                              count: quiz.question_count,
                              score: quiz.pass_score,
                              minutes: quiz.time_limit_minutes,
                            })
                          : fill(t.roadmap.quizMeta, {
                              count: quiz.question_count,
                              score: quiz.pass_score,
                            })}
                      </p>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        )}

        {phase.labs.length > 0 && (
          <section className="mt-10">
            <h2 className="text-lg font-semibold tracking-tight text-ink">
              {t.roadmap.labsHeading}
            </h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {phase.labs.map((lab) => (
                <Link key={lab.slug} href={href(`/labs/${lab.slug}`)} className="group">
                  <Card className="h-full transition-colors group-hover:border-[var(--accent)]">
                    <CardContent className="pt-5">
                      <h3 className="font-semibold text-ink">{lab.title}</h3>
                      <p className="mt-1.5 text-sm text-ink-secondary">{lab.description}</p>
                      <p className="mt-3 text-xs text-ink-muted">
                        {fill(t.roadmap.labMeta, {
                          difficulty:
                            t.labs.difficulty[
                              lab.difficulty as keyof typeof t.labs.difficulty
                            ] ?? lab.difficulty,
                          minutes: formatMinutes(lab.estimated_minutes, t.common.minutes),
                        })}
                      </p>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        )}
      </div>
    </CompletionProvider>
  );
}
