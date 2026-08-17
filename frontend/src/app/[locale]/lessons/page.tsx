import type { Metadata } from 'next';
import Link from 'next/link';

import { CompletionDot, CompletionProvider } from '@/components/completion';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { fill, getDictionary } from '@/i18n';
import { localePath, LOCALES, normalizeLocale } from '@/i18n/config';
import { serverFetch } from '@/lib/api';
import type { PhaseDetail } from '@/lib/types';
import { formatMinutes, phaseColor } from '@/lib/utils';

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

export default async function LessonsPage({ params }: { params: { locale: string } }) {
  const locale = normalizeLocale(params.locale);
  const t = getDictionary(locale);
  const href = (path: string) => localePath(path, locale);

  const phases = (await serverFetch<PhaseDetail[]>('/roadmap', locale)) ?? [];
  const totalLessons = phases.reduce(
    (sum, phase) => sum + phase.weeks.reduce((n, week) => n + week.lessons.length, 0),
    0,
  );

  return (
    <CompletionProvider>
      <div className="py-4">
        <header className="max-w-3xl">
          <h1 className="text-3xl font-semibold tracking-tight text-ink">
            {t.lessons.heading}
          </h1>
          <p className="mt-3 text-ink-secondary">
            {fill(t.lessons.intro, { count: totalLessons })}
          </p>
        </header>

        {phases.length === 0 ? (
          <Card className="mt-8">
            <CardContent className="pt-5 text-sm text-ink-muted">
              {t.lessons.empty}
            </CardContent>
          </Card>
        ) : (
          <div className="mt-10 flex flex-col gap-8">
            {phases.map((phase) => (
              <section key={phase.slug}>
                <div className="flex items-center gap-2">
                  <span
                    aria-hidden
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ background: phaseColor(phase.order_index) }}
                  />
                  <h2 className="text-lg font-semibold tracking-tight text-ink">
                    <Link href={href(`/roadmap/${phase.slug}`)} className="hover:underline">
                      {phase.title}
                    </Link>
                  </h2>
                </div>

                <ul className="mt-3 divide-y divide-[var(--border)] rounded-card border border-line bg-surface px-4">
                  {phase.weeks.flatMap((week) =>
                    week.lessons.map((lesson) => (
                      <li key={lesson.slug}>
                        <Link
                          href={href(`/lessons/${lesson.slug}`)}
                          className="flex items-center gap-3 py-3"
                        >
                          <CompletionDot slug={lesson.slug} />
                          <span className="w-20 shrink-0 text-xs text-ink-muted">
                            {fill(t.lessons.week, { number: week.number })}
                          </span>
                          <span className="flex-1 text-sm text-ink-secondary hover:text-ink">
                            {lesson.title}
                          </span>
                          {lesson.is_placeholder && (
                            <Badge variant="outline" className="shrink-0">
                              {t.common.draft}
                            </Badge>
                          )}
                          <span className="hidden shrink-0 text-xs tabular-nums text-ink-muted sm:inline">
                            {formatMinutes(lesson.estimated_minutes, t.common.minutes)}
                          </span>
                        </Link>
                      </li>
                    )),
                  )}
                </ul>
              </section>
            ))}
          </div>
        )}
      </div>
    </CompletionProvider>
  );
}
