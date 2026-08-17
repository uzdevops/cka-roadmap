'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useI18n } from '@/i18n/provider';
import { apiPublic } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { AttemptSummary, QuizSummary } from '@/lib/types';
import { formatDateLocale } from '@/lib/utils';

export default function QuizzesPage() {
  const { user, loading: authLoading } = useAuth();
  const { t, href, fill, locale } = useI18n();
  const [quizzes, setQuizzes] = useState<QuizSummary[]>([]);
  const [attempts, setAttempts] = useState<AttemptSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    let cancelled = false;

    void (async () => {
      const [quizResult, attemptResult] = await Promise.allSettled([
        apiPublic<QuizSummary[]>('/quizzes'),
        user ? apiPublic<AttemptSummary[]>('/quizzes/attempts') : Promise.resolve([]),
      ]);
      if (cancelled) return;
      if (quizResult.status === 'fulfilled') setQuizzes(quizResult.value);
      if (attemptResult.status === 'fulfilled') setAttempts(attemptResult.value);
      setLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [user, authLoading, locale]);

  return (
    <div className="py-4">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-tight text-ink">{t.quizzes.heading}</h1>
        <p className="mt-3 text-ink-secondary">{t.quizzes.intro}</p>
      </header>

      {loading ? (
        <p className="mt-10 text-sm text-ink-muted">{t.common.loading}</p>
      ) : quizzes.length === 0 ? (
        <Card className="mt-8">
          <CardContent className="pt-5 text-sm text-ink-muted">{t.quizzes.empty}</CardContent>
        </Card>
      ) : (
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {quizzes.map((quiz) => (
            <Card key={quiz.slug} className="flex flex-col">
              <CardContent className="flex flex-1 flex-col pt-5">
                <div className="flex items-start justify-between gap-3">
                  <h2 className="font-semibold text-ink">{quiz.title}</h2>
                  {quiz.best_score !== null && (
                    <Badge variant={quiz.best_score >= quiz.pass_score ? 'good' : 'critical'}>
                      {fill(t.quizzes.best, { score: quiz.best_score })}
                    </Badge>
                  )}
                </div>
                <p className="mt-2 flex-1 text-sm text-ink-secondary">{quiz.description}</p>
                <p className="mt-4 text-xs text-ink-muted">
                  {fill(t.quizzes.meta, {
                    count: quiz.question_count,
                    score: quiz.pass_score,
                  })}
                  {quiz.time_limit_minutes &&
                    ` · ${quiz.time_limit_minutes} ${t.common.minutes}`}
                  {quiz.attempt_count > 0 &&
                    ` · ${fill(t.quizzes.metaAttempts, { count: quiz.attempt_count })}`}
                </p>
                <div className="mt-4">
                  {quiz.locked ? (
                    <span className="text-sm text-ink-muted">{t.quizzes.locked}</span>
                  ) : (
                    <Link
                      href={href(`/quizzes/${quiz.slug}`)}
                      className="text-sm font-medium text-[var(--accent)] hover:underline"
                    >
                      {quiz.attempt_count > 0 ? t.quizzes.retake : t.quizzes.start}
                    </Link>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {user && attempts.length > 0 && (
        <section className="mt-12">
          <h2 className="text-lg font-semibold tracking-tight text-ink">
            {t.quizzes.attemptsHeading}
          </h2>
          <div className="mt-4 overflow-x-auto rounded-card border border-line bg-surface">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-axis text-left text-xs uppercase tracking-wide text-ink-muted">
                  <th className="px-4 py-2.5 font-medium">{t.quizzes.colQuiz}</th>
                  <th className="px-4 py-2.5 font-medium">{t.quizzes.colDate}</th>
                  <th className="px-4 py-2.5 text-right font-medium">
                    {t.quizzes.colCorrect}
                  </th>
                  <th className="px-4 py-2.5 text-right font-medium">{t.quizzes.colScore}</th>
                </tr>
              </thead>
              <tbody>
                {attempts.map((attempt) => (
                  <tr key={attempt.id} className="border-b border-line last:border-0">
                    <td className="px-4 py-2.5 text-ink">{attempt.quiz_title}</td>
                    <td className="px-4 py-2.5 text-ink-secondary">
                      {formatDateLocale(attempt.completed_at, locale)}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-ink-secondary">
                      {attempt.correct_count} / {attempt.question_count}
                    </td>
                    <td
                      className="px-4 py-2.5 text-right font-medium tabular-nums"
                      style={{
                        color: attempt.passed ? 'var(--good-text)' : 'var(--critical)',
                      }}
                    >
                      {attempt.score}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
