import Link from 'next/link';

import { ButtonLink } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { getDictionary, fill } from '@/i18n';
import { localePath, normalizeLocale } from '@/i18n/config';
import { serverFetch } from '@/lib/api';
import type { PhaseSummary } from '@/lib/types';
import { phaseColor } from '@/lib/utils';

export const dynamic = 'force-dynamic';

const DOMAIN_WEIGHTS = [
  { key: 'troubleshooting', weight: 30 },
  { key: 'cluster', weight: 25 },
  { key: 'networking', weight: 20 },
  { key: 'workloads', weight: 15 },
  { key: 'storage', weight: 10 },
] as const;

export default async function HomePage({ params }: { params: { locale: string } }) {
  const locale = normalizeLocale(params.locale);
  const t = getDictionary(locale);
  const href = (path: string) => localePath(path, locale);

  const phases = (await serverFetch<PhaseSummary[]>('/roadmap/phases', locale)) ?? [];

  return (
    <div className="flex flex-col gap-16 py-4">
      <section className="mx-auto max-w-3xl text-center">
        <p className="text-sm font-medium uppercase tracking-wide text-[var(--accent)]">
          {t.home.eyebrow}
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
          {t.home.titleLead}{' '}
          <span className="text-ink-secondary">kubectl get pods</span>{' '}
          {t.home.titleTail}
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-ink-secondary">
          {t.home.subtitle}
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <ButtonLink href={href('/register')} size="lg">
            {t.home.ctaPrimary}
          </ButtonLink>
          <ButtonLink href={href('/roadmap')} variant="outline" size="lg">
            {t.home.ctaSecondary}
          </ButtonLink>
        </div>
        <p className="mt-4 text-sm text-ink-muted">
          {t.home.demoHint}{' '}
          <code className="rounded bg-[var(--surface-2)] px-1.5 py-0.5 text-ink-secondary">
            student@demo.local
          </code>{' '}
          /{' '}
          <code className="rounded bg-[var(--surface-2)] px-1.5 py-0.5 text-ink-secondary">
            DemoPass123!
          </code>
        </p>
      </section>

      <section>
        <div className="mb-6 flex items-baseline justify-between gap-4">
          <h2 className="text-xl font-semibold tracking-tight text-ink">
            {t.home.phasesHeading}
          </h2>
          <Link href={href('/roadmap')} className="text-sm text-[var(--accent)] hover:underline">
            {t.home.fullRoadmap}
          </Link>
        </div>

        {phases.length === 0 ? (
          <Card>
            <CardContent className="pt-5 text-sm text-ink-muted">
              {t.common.apiUnavailable}
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {phases.map((phase) => (
              <Link key={phase.slug} href={href(`/roadmap/${phase.slug}`)} className="group">
                <Card className="h-full transition-colors group-hover:border-[var(--accent)]">
                  <CardContent className="flex h-full flex-col pt-5">
                    <div className="flex items-center gap-2">
                      {/* Identity dot, always beside the phase name - never colour alone. */}
                      <span
                        aria-hidden
                        className="h-2.5 w-2.5 shrink-0 rounded-full"
                        style={{ background: phaseColor(phase.order_index) }}
                      />
                      <span className="text-xs font-medium uppercase tracking-wide text-ink-muted">
                        {fill(t.home.weeksRange, {
                          start: phase.week_start,
                          end: phase.week_end,
                        })}
                        {phase.exam_weight > 0 &&
                          ` · ${fill(t.home.examWeight, { weight: phase.exam_weight })}`}
                      </span>
                    </div>
                    <h3 className="mt-3 font-semibold text-ink">{phase.title}</h3>
                    <p className="mt-2 line-clamp-4 flex-1 text-sm text-ink-secondary">
                      {phase.description}
                    </p>
                    <p className="mt-4 text-xs text-ink-muted">
                      {phase.total_lessons} {t.common.lessons}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        {t.home.features.map((feature) => (
          <Card key={feature.title}>
            <CardContent className="pt-5">
              <h3 className="font-semibold text-ink">{feature.title}</h3>
              <p className="mt-2 text-sm text-ink-secondary">{feature.body}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <section>
        <h2 className="text-xl font-semibold tracking-tight text-ink">
          {t.home.weighingHeading}
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-ink-secondary">{t.home.weighingBody}</p>
        <ul className="mt-6 flex flex-col gap-3">
          {DOMAIN_WEIGHTS.map((domain) => (
            <li key={domain.key}>
              <div className="mb-1.5 flex items-baseline justify-between gap-3">
                <span className="text-sm text-ink">{t.home.domains[domain.key]}</span>
                <span className="shrink-0 text-sm font-semibold tabular-nums text-ink">
                  {domain.weight}%
                </span>
              </div>
              <div
                className="h-2.5 w-full overflow-hidden rounded-full"
                style={{ background: 'var(--track)' }}
              >
                <div
                  className="h-full"
                  style={{
                    width: `${(domain.weight / 30) * 100}%`,
                    background: 'var(--accent)',
                    borderRadius: '0 4px 4px 0',
                  }}
                />
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
