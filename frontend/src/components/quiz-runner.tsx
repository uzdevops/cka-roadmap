'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/field';
import { Meter } from '@/components/ui/meter';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { QuizDetail, QuizResult } from '@/lib/types';
import { cn } from '@/lib/utils';

type Answers = Record<number, { selected: string[]; text: string }>;

export function QuizRunner({ quiz }: { quiz: QuizDetail }) {
  const { user } = useAuth();
  const { t, href, fill } = useI18n();
  const [answers, setAnswers] = useState<Answers>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const answeredCount = useMemo(
    () =>
      quiz.questions.filter((q) => {
        const a = answers[q.id];
        if (!a) return false;
        return q.type === 'fill_command' ? a.text.trim().length > 0 : a.selected.length > 0;
      }).length,
    [answers, quiz.questions],
  );

  const setSelected = (questionId: number, optionId: string, multi: boolean) => {
    setAnswers((prev) => {
      const current = prev[questionId] ?? { selected: [], text: '' };
      const selected = multi
        ? current.selected.includes(optionId)
          ? current.selected.filter((id) => id !== optionId)
          : [...current.selected, optionId]
        : [optionId];
      return { ...prev, [questionId]: { ...current, selected } };
    });
  };

  const setText = (questionId: number, text: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: { selected: prev[questionId]?.selected ?? [], text },
    }));
  };

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const payload = {
        answers: quiz.questions.map((question) => ({
          question_id: question.id,
          selected_options: answers[question.id]?.selected ?? [],
          text_answer: answers[question.id]?.text ?? null,
        })),
      };
      const data = await apiFetch<QuizResult>(`/quizzes/${quiz.slug}/submit`, {
        method: 'POST',
        body: payload,
      });
      setResult(data);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err instanceof Error ? err.message : t.quizzes.submitError);
    } finally {
      setBusy(false);
    }
  };

  const retake = () => {
    setResult(null);
    setAnswers({});
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (result) {
    return <QuizResultView quiz={quiz} result={result} onRetake={retake} />;
  }

  return (
    <div className="py-4">
      <Link href={href('/quizzes')} className="text-sm text-ink-muted hover:text-ink">
        {t.quizzes.backToQuizzes}
      </Link>

      <header className="mt-4 max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-tight text-ink">{quiz.title}</h1>
        <p className="mt-3 text-ink-secondary">{quiz.description}</p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Badge variant="outline">
            {quiz.questions.length} {t.common.questions}
          </Badge>
          <Badge variant="outline">
            {fill(t.quizzes.meta, { count: quiz.questions.length, score: quiz.pass_score })}
          </Badge>
          {quiz.time_limit_minutes && (
            <Badge variant="outline">
              {quiz.time_limit_minutes} {t.common.minutes}
            </Badge>
          )}
        </div>
      </header>

      <div className="sticky top-14 z-20 -mx-4 mt-8 border-y border-line bg-[var(--plane)]/95 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-4">
          <span className="shrink-0 text-sm tabular-nums text-ink-secondary">
            {fill(t.quizzes.answered, {
              answered: answeredCount,
              total: quiz.questions.length,
            })}
          </span>
          <Meter
            value={(answeredCount / Math.max(1, quiz.questions.length)) * 100}
            label={t.quizzes.answered}
            className="flex-1"
            height={6}
          />
        </div>
      </div>

      <ol className="mt-8 flex flex-col gap-5">
        {quiz.questions.map((question, index) => {
          const answer = answers[question.id] ?? { selected: [], text: '' };
          const multi = question.type === 'multi_select';

          return (
            <li key={question.id}>
              <Card>
                <CardContent className="pt-5">
                  <div className="flex items-baseline gap-3">
                    <span className="shrink-0 text-sm tabular-nums text-ink-muted">
                      {index + 1}.
                    </span>
                    <div className="flex-1">
                      <p className="font-medium text-ink">{question.prompt}</p>
                      <p className="mt-1 text-xs text-ink-muted">
                        {question.type === 'single_choice' && t.quizzes.chooseOne}
                        {multi && t.quizzes.chooseAll}
                        {question.type === 'fill_command' && t.quizzes.typeCommand}
                        {question.points > 1 &&
                          ` · ${fill(t.quizzes.points, { count: question.points })}`}
                      </p>

                      {question.type === 'fill_command' ? (
                        <Input
                          className="mt-3 font-mono"
                          spellCheck={false}
                          autoCapitalize="off"
                          autoCorrect="off"
                          placeholder="kubectl ..."
                          value={answer.text}
                          onChange={(e) => setText(question.id, e.target.value)}
                        />
                      ) : (
                        <ul className="mt-3 flex flex-col gap-2">
                          {question.options.map((option) => {
                            const checked = answer.selected.includes(option.id);
                            return (
                              <li key={option.id}>
                                <label
                                  className={cn(
                                    'flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm transition-colors',
                                    checked
                                      ? 'border-[var(--accent)] bg-[var(--surface-2)]'
                                      : 'border-line hover:bg-[var(--surface-2)]',
                                  )}
                                >
                                  <input
                                    type={multi ? 'checkbox' : 'radio'}
                                    name={`q-${question.id}`}
                                    className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--accent)]"
                                    checked={checked}
                                    onChange={() => setSelected(question.id, option.id, multi)}
                                  />
                                  <span className="text-ink-secondary">{option.text}</span>
                                </label>
                              </li>
                            );
                          })}
                        </ul>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </li>
          );
        })}
      </ol>

      <div className="mt-8 max-w-prose">
        {!user ? (
          <Card>
            <CardContent className="pt-5 text-sm text-ink-secondary">
              <Link
                href={href(`/login?next=/quizzes/${quiz.slug}`)}
                className="text-[var(--accent)] hover:underline"
              >
                {t.lessons.signInLink}
              </Link>{' '}
              {t.quizzes.signInPrompt}
            </CardContent>
          </Card>
        ) : (
          <>
            <Button size="lg" onClick={submit} disabled={busy}>
              {busy ? t.quizzes.grading : t.quizzes.submit}
            </Button>
            {answeredCount < quiz.questions.length && (
              <p className="mt-3 text-sm text-ink-muted">
                {fill(t.quizzes.unanswered, {
                  count: quiz.questions.length - answeredCount,
                })}
              </p>
            )}
            {error && (
              <p role="alert" className="mt-3 text-sm text-[var(--critical)]">
                {error}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function QuizResultView({
  quiz,
  result,
  onRetake,
}: {
  quiz: QuizDetail;
  result: QuizResult;
  onRetake: () => void;
}) {
  const { t, href, fill } = useI18n();

  const optionText = (questionId: number, optionId: string) => {
    const question = quiz.questions.find((q) => q.id === questionId);
    return question?.options.find((o) => o.id === optionId)?.text ?? optionId;
  };

  return (
    <div className="py-4">
      <Link href={href('/quizzes')} className="text-sm text-ink-muted hover:text-ink">
        {t.quizzes.backToQuizzes}
      </Link>

      <Card className="mt-4">
        <CardContent className="pt-6">
          <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">
            {result.quiz_title}
          </p>
          <div className="mt-2 flex flex-wrap items-end gap-x-6 gap-y-2">
            <p
              className="text-6xl font-semibold leading-none tracking-tight"
              style={{ color: result.passed ? 'var(--good-text)' : 'var(--critical)' }}
            >
              {result.score.toFixed(0)}
              <span className="ml-1 text-2xl font-medium text-ink-muted">%</span>
            </p>
            <div className="mb-1">
              <p className="font-medium text-ink">
                {result.passed
                  ? t.quizzes.passed
                  : fill(t.quizzes.failed, { score: quiz.pass_score })}
              </p>
              <p className="text-sm text-ink-secondary">
                {fill(t.quizzes.resultSummary, {
                  correct: result.correct_count,
                  total: result.question_count,
                  earned: result.earned_points,
                  possible: result.total_points,
                })}
              </p>
            </div>
          </div>

          <div className="mt-5">
            <Meter value={result.score} label={t.quizzes.colScore} height={10} />
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button onClick={onRetake} variant="secondary">
              {t.quizzes.retakeButton}
            </Button>
            <Link
              href={href('/dashboard')}
              className="inline-flex h-10 items-center rounded-lg px-4 text-sm text-[var(--accent)] hover:underline"
            >
              {t.quizzes.toDashboard}
            </Link>
          </div>
        </CardContent>
      </Card>

      <h2 className="mt-10 text-lg font-semibold tracking-tight text-ink">
        {t.quizzes.reviewHeading}
      </h2>

      <ol className="mt-4 flex flex-col gap-4">
        {result.results.map((answer, index) => (
          <li key={answer.question_id}>
            <Card
              style={{
                borderLeftWidth: 3,
                borderLeftColor: answer.is_correct ? 'var(--good)' : 'var(--critical)',
              }}
            >
              <CardContent className="pt-5">
                <div className="flex items-baseline gap-3">
                  <span className="shrink-0 text-sm tabular-nums text-ink-muted">
                    {index + 1}.
                  </span>
                  <div className="flex-1">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <p className="font-medium text-ink">{answer.prompt}</p>
                      <Badge variant={answer.is_correct ? 'good' : 'critical'}>
                        {answer.is_correct
                          ? `✓ ${answer.points_earned}/${answer.points_possible}`
                          : `✕ 0/${answer.points_possible}`}
                      </Badge>
                    </div>

                    <dl className="mt-3 flex flex-col gap-2 text-sm">
                      <div className="flex flex-wrap gap-x-2">
                        <dt className="text-ink-muted">{t.quizzes.yourAnswer}</dt>
                        <dd className="text-ink-secondary">
                          {answer.given.filter(Boolean).length === 0
                            ? t.quizzes.notAnswered
                            : answer.type === 'fill_command'
                              ? answer.given.map((g) => (
                                  <code key={g} className="font-mono">
                                    {g}
                                  </code>
                                ))
                              : answer.given
                                  .map((id) => optionText(answer.question_id, id))
                                  .join(', ')}
                        </dd>
                      </div>

                      {!answer.is_correct && (
                        <div className="flex flex-wrap gap-x-2">
                          <dt className="text-ink-muted">{t.quizzes.correctAnswer}</dt>
                          <dd className="text-ink-secondary">
                            {answer.type === 'fill_command'
                              ? answer.correct.map((c) => (
                                  <code key={c} className="mr-2 font-mono">
                                    {c}
                                  </code>
                                ))
                              : answer.correct
                                  .map((id) => optionText(answer.question_id, id))
                                  .join(', ')}
                          </dd>
                        </div>
                      )}
                    </dl>

                    {answer.explanation && (
                      <p className="mt-3 border-t border-line pt-3 text-sm text-ink-secondary">
                        {answer.explanation}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </li>
        ))}
      </ol>
    </div>
  );
}
