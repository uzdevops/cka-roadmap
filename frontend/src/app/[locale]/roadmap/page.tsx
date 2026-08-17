import type { Metadata } from 'next';
import Link from 'next/link';

import { CompletionProvider, WeekProgress } from '@/components/completion';
import { Card, CardContent } from '@/components/ui/card';
import { fill, getDictionary } from '@/i18n';
import { localePath, LOCALES, normalizeLocale } from '@/i18n/config';
import { serverFetch } from '@/lib/server-api';
import type { PhaseDetail } from '@/lib/types';
import { phaseColor } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const locale = normalizeLocale(params.locale);
  const t = getDictionary(locale);
  return {
    title: t.meta.roadmapTitle,
    description: t.meta.roadmapDescription,
    alternates: {
      canonical: `/${locale}/roadmap`,
      languages: Object.fromEntries(LOCALES.map((l) => [l, `/${l}/roadmap`])),
    },
  };
}

export default async function RoadmapPage({ params }: { params: { locale: string } }) {
  const locale = normalizeLocale(params.locale);
  const t = getDictionary(locale);
  const href = (path: string) => localePath(path, locale);

  const phases = (await serverFetch<PhaseDetail[]>('/roadmap', locale)) ?? [];

  return (
    <CompletionProvider>
      <div className="py-4">
        <header className="max-w-3xl">
          <h1 className="text-3xl font-semibold tracking-tight text-ink">
            {t.roadmap.heading}
          </h1>
          <p className="mt-3 text-ink-secondary">{t.roadmap.intro}</p>
        </header>

        {phases.length === 0 ? (
          <Card className="mt-8">
            <CardContent className="pt-5 text-sm text-ink-muted">
              {t.roadmap.empty}
            </CardContent>
          </Card>
        ) : (
          <div className="mt-10 flex flex-col gap-10">
            {phases.map((phase) => (
              <section key={phase.slug} id={phase.slug}>
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span
                    aria-hidden
                    className="h-3 w-3 self-center rounded-full"
                    style={{ background: phaseColor(phase.order_index) }}
                  />
                  <h2 className="text-xl font-semibold tracking-tight text-ink">
                    <Link href={href(`/roadmap/${phase.slug}`)} className="hover:underline">
                      {phase.title}
                    </Link>
                  </h2>
                  <span className="text-sm text-ink-muted">
                    {fill(t.home.weeksRange, {
                      start: phase.week_start,
                      end: phase.week_end,
                    })}
                    {phase.exam_weight > 0 &&
                      ` · ${fill(t.home.examWeight, { weight: phase.exam_weight })}`}
                  </span>
                </div>

                <p className="mt-2 max-w-3xl text-sm text-ink-secondary">{phase.description}</p>

                <div className="mt-5 grid gap-3 md:grid-cols-2">
                  {phase.weeks.map((week) => (
                    <Card key={week.id}>
                      <CardContent className="pt-5">
                        <div className="flex items-baseline justify-between gap-3">
                          <h3 className="text-sm font-semibold text-ink">{week.title}</h3>
                          <WeekProgress slugs={week.lessons.map((l) => l.slug)} />
                        </div>
                        {week.description && (
                          <p className="mt-1.5 text-sm text-ink-secondary">{week.description}</p>
                        )}
                        <ul className="mt-3 flex flex-col gap-1.5">
                          {week.lessons.map((lesson) => (
                            <li key={lesson.slug}>
                              <Link
                                href={href(`/lessons/${lesson.slug}`)}
                                className="flex items-baseline gap-2 text-sm text-ink-secondary hover:text-ink"
                              >
                                <span aria-hidden className="text-ink-muted">
                                  ·
                                </span>
                                <span className="flex-1">{lesson.title}</span>
                                {lesson.is_placeholder && (
                                  <span className="shrink-0 text-xs text-ink-muted">
                                    {t.common.draft}
                                  </span>
                                )}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </div>
    </CompletionProvider>
  );
}
