'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { PhaseProgressChart } from '@/components/charts/phase-progress-chart';
import { ReadinessPanel } from '@/components/charts/readiness-panel';
import { ScoreTrendChart } from '@/components/charts/score-trend-chart';
import { StatTile } from '@/components/charts/stat-tile';
import { ProgressRing } from '@/components/dashboard/progress-ring';
import { WeekGrid, WeekStatusBar } from '@/components/dashboard/week-grid';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { Dashboard, PhaseDetail } from '@/lib/types';
import { buildWeeks, tallyWeeks } from '@/lib/weeks';

/**
 * The signed-in view, shared by `/` and `/dashboard`.
 *
 * Two requests on purpose: `/progress/dashboard` carries the aggregates, while
 * `/roadmap` carries the week-by-week structure the tracker needs. Neither
 * endpoint knows about the other, and neither had to change.
 */
export function DashboardView() {
  const { user } = useAuth();
  const { t, href, fill, locale } = useI18n();

  const [data, setData] = useState<Dashboard | null>(null);
  const [phases, setPhases] = useState<PhaseDetail[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void Promise.all([
      apiFetch<Dashboard>('/progress/dashboard'),
      apiFetch<PhaseDetail[]>('/roadmap'),
    ])
      .then(([dashboard, roadmap]) => {
        if (cancelled) return;
        setData(dashboard);
        setPhases(roadmap);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed');
      });

    return () => {
      cancelled = true;
    };
  }, [locale]);

  if (error) {
    return <p className="py-16 text-center text-sm text-[var(--critical)]">{error}</p>;
  }

  if (!data || !phases) {
    return <p className="py-16 text-center text-sm text-ink-muted">{t.dashboard.loading}</p>;
  }

  const weeks = buildWeeks(phases);
  const tally = tallyWeeks(weeks);

  const days = (n: number) =>
    fill(n === 1 ? t.lessons.streakDay : t.lessons.streakDays, { count: n });

  const streakHint =
    data.streak.current_streak === 0
      ? t.dashboard.statStreakEmpty
      : fill(t.dashboard.statStreakHint, { value: days(data.streak.longest_streak) });

  return (
    <div className="py-4">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">
          {user?.full_name
            ? fill(t.dashboard.headingOwn, { name: user.full_name.split(' ')[0] })
            : t.dashboard.heading}
        </h1>
        <p className="mt-2 text-ink-secondary">{t.dashboard.intro}</p>
      </header>

      {/* Three bands rather than two columns: the twenty week cards want the
          full width far more than the stat tiles want their own column. */}
      <div className="mt-6 flex flex-col gap-5">
        <div className="grid gap-5 xl:grid-cols-3">
          {/* Hero: one ring, one twenty-segment bar. */}
          <Card className="dash-hero xl:col-span-2">
            <CardContent className="flex h-full flex-col justify-between gap-8 pt-6">
              <div className="flex flex-wrap items-center gap-x-8 gap-y-6">
                <ProgressRing
                  value={data.overall_percent}
                  label={t.dashboard.trackerHeading}
                  caption={t.dashboard.ringCaption}
                />

                <div className="min-w-[15rem] flex-1">
                  <h2 className="text-xs font-medium uppercase tracking-wide text-ink-muted">
                    {t.dashboard.trackerHeading}
                  </h2>
                  <p className="mt-2 text-2xl font-semibold leading-tight text-ink">
                    {fill(t.dashboard.trackerLessons, {
                      done: data.completed_lessons,
                      total: data.total_lessons,
                    })}
                  </p>

                  <dl className="mt-4 flex flex-wrap gap-x-6 gap-y-2">
                    {(
                      [
                        ['complete', tally.complete, t.dashboard.weekComplete],
                        ['active', tally.active, t.dashboard.weekActive],
                        ['pending', tally.pending, t.dashboard.weekPending],
                      ] as const
                    ).map(([state, count, label]) => (
                      <div key={state} className="flex items-center gap-2">
                        <span aria-hidden className={`dash-key dash-key-${state}`} />
                        <dt className="text-xs text-ink-secondary">{label}</dt>
                        <dd className="text-sm font-semibold tabular-nums text-ink">{count}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </div>

              <div className="mt-6">
                <WeekStatusBar weeks={weeks} />
              </div>
            </CardContent>
          </Card>

          {/* Stat tiles, beside the hero rather than under it. */}
          <div className="grid gap-4 sm:grid-cols-2 xl:gap-4">
            <StatTile
            label={t.dashboard.statLessons}
            value={`${data.completed_lessons} / ${data.total_lessons}`}
            hint={fill(t.dashboard.statLessonsHint, { percent: data.overall_percent })}
          />
          <StatTile
            label={t.dashboard.statStreak}
            value={days(data.streak.current_streak)}
            hint={streakHint}
            tone={data.streak.current_streak >= 3 ? 'good' : 'default'}
          />
          <StatTile
            label={t.dashboard.statQuizAvg}
            value={data.quiz_average === null ? '—' : `${data.quiz_average}%`}
            hint={
              data.attempted_quizzes === 0
                ? t.dashboard.statQuizAvgEmpty
                : fill(t.dashboard.statQuizAvgHint, {
                    attempted: data.attempted_quizzes,
                    total: data.total_quizzes,
                  })
            }
          />
          {data.target_exam_date ? (
            <StatTile
              label={t.dashboard.statCountdown}
              value={data.days_until_exam ?? '—'}
              hint={fill(t.dashboard.statCountdownHint, {
                date: data.target_exam_date,
                done: data.completed_labs,
                total: data.total_labs,
              })}
              tone={
                data.days_until_exam !== null && data.days_until_exam < 14
                  ? 'critical'
                  : 'default'
              }
            />
          ) : (
            <StatTile
              label={t.dashboard.statLabs}
              value={`${data.completed_labs} / ${data.total_labs}`}
              hint={
                <Link href={href('/profile')} className="text-[var(--accent)] hover:underline">
                  {t.dashboard.statLabsHint}
                </Link>
              }
            />
          )}
          </div>
        </div>

        {/* Twenty cards want the whole width: five across beats three. */}
        <Card>
          <CardHeader>
            <CardTitle>{t.dashboard.weeksHeading}</CardTitle>
          </CardHeader>
          <CardContent>
            <WeekGrid weeks={weeks} />
          </CardContent>
        </Card>

        <div className="grid gap-5 xl:grid-cols-3">
          <Card className="xl:col-span-2">
            <CardContent className="pt-6">
              <ReadinessPanel readiness={data.readiness} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t.dashboard.scoreChartTitle}</CardTitle>
            </CardHeader>
            <CardContent>
              <ScoreTrendChart points={data.recent_scores} />
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-5 xl:grid-cols-3">
          <Card className="xl:col-span-2">
            <CardHeader>
              <CardTitle>{t.dashboard.phaseChartTitle}</CardTitle>
            </CardHeader>
            <CardContent>
              <PhaseProgressChart phases={data.phases} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t.dashboard.nextHeading}</CardTitle>
            </CardHeader>
            <CardContent>
              <NextSteps data={data} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Bullet({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex gap-3">
      <span aria-hidden className="text-ink-muted">
        →
      </span>
      <span className="text-ink-secondary">{children}</span>
    </li>
  );
}

function NextSteps({ data }: { data: Dashboard }) {
  const { t, href, fill } = useI18n();

  const weakest = [...data.phases]
    .filter((p) => p.exam_weight > 0)
    .sort((a, b) => (a.quiz_average ?? 0) - (b.quiz_average ?? 0))[0];

  const nextPhase = data.phases.find((p) => p.progress_percent < 100);

  return (
    <ul className="flex flex-col gap-3 text-sm">
      {nextPhase && (
        <Bullet>
          {t.dashboard.nextContinuePrefix}{' '}
          <Link
            href={href(`/roadmap/${nextPhase.phase_slug}`)}
            className="text-[var(--accent)] hover:underline"
          >
            {nextPhase.phase_title}
          </Link>{' '}
          {fill(t.dashboard.nextContinueSuffix, {
            done: nextPhase.completed_lessons,
            total: nextPhase.total_lessons,
          })}
        </Bullet>
      )}

      {data.attempted_quizzes === 0 ? (
        <Bullet>
          <Link href={href('/quizzes')} className="text-[var(--accent)] hover:underline">
            {t.dashboard.quizWord}
          </Link>{' '}
          — {t.dashboard.nextFirstQuiz}
        </Bullet>
      ) : (
        weakest && (
          <Bullet>
            {fill(t.dashboard.nextWeakest, {
              phase: weakest.phase_title,
              weight: weakest.exam_weight,
              score:
                weakest.quiz_average === null
                  ? t.dashboard.nextWeakestNoAttempts
                  : fill(t.dashboard.nextWeakestAverage, { score: weakest.quiz_average }),
            })}
          </Bullet>
        )
      )}

      {data.completed_labs < data.total_labs && (
        <Bullet>
          <Link href={href('/labs')} className="text-[var(--accent)] hover:underline">
            {t.dashboard.labsWord}
          </Link>{' '}
          — {fill(t.dashboard.nextLabs, { count: data.total_labs - data.completed_labs })}
        </Bullet>
      )}

      {data.streak.current_streak === 0 && (
        <Bullet>{fill(t.dashboard.nextStreak, { minutes: data.daily_study_minutes })}</Bullet>
      )}
    </ul>
  );
}
