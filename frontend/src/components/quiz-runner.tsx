'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button, ButtonLink } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/field';
import { Meter } from '@/components/ui/meter';
import type { Dictionary } from '@/i18n';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { QuestionType, QuizDetail, QuizResult } from '@/lib/types';
import { cn } from '@/lib/utils';

type Answers = Record<number, { selected: string[]; text: string }>;

const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

/** A, B, C ... - a stable handle for an option that is not its opaque id. */
const optionKey = (index: number) => LETTERS[index] ?? String(index + 1);

/** Question counters line up in a column, so they are zero padded. */
const pad = (n: number) => String(n).padStart(2, '0');

/** The one-line instruction for a question type. Always from the dictionary. */
function typeHint(t: Dictionary, type: QuestionType): string {
  if (type === 'single_choice') return t.quizzes.chooseOne;
  if (type === 'multi_select') return t.quizzes.chooseAll;
  return t.quizzes.typeCommand;
}

function Dot() {
  return (
    <span aria-hidden className="text-ink-muted">
      ·
    </span>
  );
}

/** A question counts as answered once it has a pick, or a non-blank command. */
function hasAnswer(
  entry: { selected: string[]; text: string } | undefined,
  type: QuestionType,
): boolean {
  if (!entry) return false;
  return type === 'fill_command' ? entry.text.trim().length > 0 : entry.selected.length > 0;
}

export function QuizRunner({
  quiz,
  onResult,
}: {
  quiz: QuizDetail;
  /** Fires after every graded submission, so the lesson can update its gate. */
  onResult?: (result: QuizResult) => void;
}) {
  const { user } = useAuth();
  const { t, href, fill } = useI18n();
  const [answers, setAnswers] = useState<Answers>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const answeredCount = useMemo(
    () => quiz.questions.filter((q) => hasAnswer(answers[q.id], q.type)).length,
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
      onResult?.(data);
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

  const total = quiz.questions.length;

  return (
    <div>
      <header className="max-w-3xl">
        <p className="tech-label">{t.nav.quizzes}</p>
        <h1 className="mt-2 text-[28px] font-bold leading-[1.15] tracking-[-0.02em] text-ink">
          {quiz.title}
        </h1>
        <p className="mt-3 text-ink-secondary">{quiz.description}</p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Badge variant="accent">{fill(t.quizzes.meta, { count: total, score: quiz.pass_score })}</Badge>
          {quiz.time_limit_minutes && (
            <Badge variant="outline">
              {quiz.time_limit_minutes} {t.common.minutes}
            </Badge>
          )}
        </div>
      </header>

      {/* Answer telemetry: count, meter, and a jump grid for long quizzes. */}
      <div className="quiz-progress sticky top-12 z-20 mt-7 rounded-card border border-line px-4 py-3">
        <div className="flex items-center gap-4">
          <span className="tech-label shrink-0 tabular-nums">
            {fill(t.quizzes.answered, { answered: answeredCount, total })}
          </span>
          <Meter
            value={(answeredCount / Math.max(1, total)) * 100}
            label={t.quizzes.answered}
            className="flex-1"
            height={6}
          />
        </div>

        <nav aria-label={t.quizzes.questionNav} className="mt-3 hidden flex-wrap gap-1.5 sm:flex">
          {quiz.questions.map((question, index) => (
            <a
              key={question.id}
              href={`#quiz-q-${question.id}`}
              aria-label={fill(t.quizzes.questionLabel, { n: index + 1 })}
              className={cn(
                'quiz-chip',
                hasAnswer(answers[question.id], question.type) && 'quiz-chip-done',
              )}
            >
              <span aria-hidden>{pad(index + 1)}</span>
            </a>
          ))}
        </nav>
      </div>

      <ol className="mt-6 flex flex-col gap-4">
        {quiz.questions.map((question, index) => {
          const answer = answers[question.id] ?? { selected: [], text: '' };
          const multi = question.type === 'multi_select';

          return (
            <li key={question.id} id={`quiz-q-${question.id}`} className="quiz-q">
              <Card>
                <CardContent className="pt-5">
                  <p className="tech-label flex flex-wrap items-center gap-x-2 gap-y-1">
                    <span className="tabular-nums">
                      {pad(index + 1)} / {pad(total)}
                    </span>
                    <Dot />
                    <span>{typeHint(t, question.type)}</span>
                    {question.points > 1 && (
                      <>
                        <Dot />
                        <span className="tabular-nums">
                          {fill(t.quizzes.points, { count: question.points })}
                        </span>
                      </>
                    )}
                  </p>

                  <p
                    id={`quiz-p-${question.id}`}
                    className="mt-2 text-[15px] font-semibold leading-relaxed text-ink"
                  >
                    {question.prompt}
                  </p>

                  {question.type === 'fill_command' ? (
                    <div className="quiz-cmd mt-4 max-w-xl">
                      <span aria-hidden className="quiz-cmd-sigil">
                        $
                      </span>
                      <Input
                        className="quiz-cmd-input"
                        spellCheck={false}
                        autoCapitalize="off"
                        autoCorrect="off"
                        autoComplete="off"
                        aria-labelledby={`quiz-p-${question.id}`}
                        placeholder="kubectl ..."
                        value={answer.text}
                        onChange={(e) => setText(question.id, e.target.value)}
                      />
                    </div>
                  ) : (
                    <ul className="mt-4 flex flex-col gap-2">
                      {question.options.map((option, optionIndex) => {
                        const checked = answer.selected.includes(option.id);
                        return (
                          <li key={option.id}>
                            <label
                              className={cn(
                                'quiz-option quiz-option-live',
                                checked && 'quiz-option-selected',
                              )}
                            >
                              <input
                                type={multi ? 'checkbox' : 'radio'}
                                name={`q-${question.id}`}
                                className="quiz-option-input"
                                checked={checked}
                                onChange={() => setSelected(question.id, option.id, multi)}
                              />
                              <span
                                aria-hidden
                                className={cn(
                                  'quiz-option-key',
                                  !multi && 'quiz-option-key-round',
                                )}
                              >
                                {optionKey(optionIndex)}
                              </span>
                              <span className="quiz-option-body">
                                <span className="quiz-option-text">{option.text}</span>
                                <span
                                  aria-hidden
                                  className={cn(
                                    'quiz-option-tick',
                                    checked && 'quiz-option-tick-on',
                                  )}
                                >
                                  ✓
                                </span>
                              </span>
                            </label>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </li>
          );
        })}
      </ol>

      <div className="mt-7 max-w-prose">
        {!user ? (
          <Card>
            <CardContent className="pt-5 text-sm text-ink-secondary">
              <Link
                href={href(`/login?next=/quizzes/${quiz.slug}`)}
                className="text-[var(--accent)] underline decoration-[var(--accent)]/40 underline-offset-2 hover:decoration-[var(--accent)]"
              >
                {t.lessons.signInLink}
              </Link>{' '}
              {t.quizzes.signInPrompt}
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <Button variant="primary" size="lg" onClick={submit} disabled={busy}>
                {busy ? t.quizzes.grading : t.quizzes.submit}
              </Button>
              {answeredCount < total && (
                <p className="text-sm text-ink-muted">
                  {fill(t.quizzes.unanswered, { count: total - answeredCount })}
                </p>
              )}
            </div>
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

  const passMark = Math.max(0, Math.min(100, quiz.pass_score));
  const total = result.results.length;

  return (
    <div>
      <section className="panel-glass rounded-card p-6">
        <p className="tech-label">{result.quiz_title}</p>

        <div className="mt-3 flex flex-wrap items-end gap-x-8 gap-y-4">
          <p
            className={cn(
              'quiz-score',
              result.passed ? 'quiz-score-pass' : 'quiz-score-fail',
            )}
          >
            {result.score.toFixed(0)}
            <span className="quiz-score-unit">%</span>
          </p>
          <div className="pb-1">
            <Badge variant={result.passed ? 'good' : 'critical'}>
              <span aria-hidden>{result.passed ? '✓' : '✕'}</span>
              {result.passed ? t.quizzes.passed : fill(t.quizzes.failed, { score: quiz.pass_score })}
            </Badge>
            <p className="mt-2 text-sm text-ink-secondary">
              {fill(t.quizzes.resultSummary, {
                correct: result.correct_count,
                total: result.question_count,
                earned: result.earned_points,
                possible: result.total_points,
              })}
            </p>
          </div>
        </div>

        {/* The bar plus the pass mark it had to clear. */}
        <div className="quiz-meter mt-6">
          <Meter value={result.score} label={t.quizzes.colScore} height={10} />
          <span aria-hidden className="quiz-passmark" style={{ left: `${passMark}%` }} />
        </div>
        <p className="tech-label mt-2 tabular-nums">
          {fill(t.quizzes.passMark, { score: quiz.pass_score })}
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Button onClick={onRetake} variant="secondary">
            {t.quizzes.retakeButton}
          </Button>
          <ButtonLink href={href('/dashboard')} variant="ghost">
            {t.quizzes.toDashboard}
          </ButtonLink>
        </div>
      </section>

      <h2 className="mt-9 text-lg font-semibold tracking-tight text-ink">
        {t.quizzes.reviewHeading}
      </h2>

      <ol className="mt-4 flex flex-col gap-4">
        {result.results.map((answer, index) => {
          const question = quiz.questions.find((q) => q.id === answer.question_id);
          const given = answer.given.filter(Boolean);
          const showOptionCards = answer.type !== 'fill_command' && (question?.options.length ?? 0) > 0;

          return (
            <li key={answer.question_id}>
              <Card
                className={cn(
                  'quiz-review',
                  answer.is_correct ? 'quiz-review-good' : 'quiz-review-bad',
                )}
              >
                <CardContent className="pt-5">
                  <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
                    <p className="tech-label flex flex-wrap items-center gap-x-2 gap-y-1">
                      <span className="tabular-nums">
                        {pad(index + 1)} / {pad(total)}
                      </span>
                      <Dot />
                      <span>{typeHint(t, answer.type)}</span>
                    </p>
                    <Badge variant={answer.is_correct ? 'good' : 'critical'}>
                      <span aria-hidden>{answer.is_correct ? '✓' : '✕'}</span>
                      <span className="tabular-nums">
                        {answer.points_earned}/{answer.points_possible}
                      </span>
                    </Badge>
                  </div>

                  <p className="mt-2 text-[15px] font-semibold leading-relaxed text-ink">
                    {answer.prompt}
                  </p>

                  {/* Nothing was picked: the option cards alone would not say so. */}
                  {showOptionCards && given.length === 0 && (
                    <p className="tech-label mt-3">
                      {t.quizzes.yourAnswer} {t.quizzes.notAnswered}
                    </p>
                  )}

                  {showOptionCards ? (
                    <ul
                      className={cn(
                        'flex flex-col gap-2',
                        given.length === 0 ? 'mt-3' : 'mt-4',
                      )}
                    >
                      {(question?.options ?? []).map((option, optionIndex) => {
                        const isRight = answer.correct.includes(option.id);
                        const isGiven = given.includes(option.id);
                        const marker = isGiven
                          ? isRight
                            ? `${t.quizzes.optionYours} · ${t.quizzes.optionCorrect}`
                            : t.quizzes.optionYours
                          : isRight
                            ? t.quizzes.optionCorrect
                            : null;

                        return (
                          <li key={option.id}>
                            <div
                              className={cn(
                                'quiz-option',
                                isRight && 'quiz-option-good',
                                !isRight && isGiven && 'quiz-option-bad',
                                !isRight && !isGiven && 'quiz-option-idle',
                              )}
                            >
                              <span
                                aria-hidden
                                className={cn(
                                  'quiz-option-key',
                                  answer.type === 'single_choice' && 'quiz-option-key-round',
                                )}
                              >
                                {optionKey(optionIndex)}
                              </span>
                              <span className="quiz-option-body">
                                <span className="quiz-option-text">{option.text}</span>
                                {marker && (
                                  <span
                                    className={cn(
                                      'quiz-marker',
                                      isRight ? 'quiz-marker-good' : 'quiz-marker-bad',
                                    )}
                                  >
                                    <span aria-hidden>{isRight ? '✓' : '✕'}</span>
                                    {marker}
                                  </span>
                                )}
                              </span>
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    /* Fill-in-the-command, or a question whose options are no
                       longer in the payload: fall back to the plain listing so
                       nothing is lost. */
                    <dl className="mt-4 flex flex-col gap-3">
                      <div>
                        <dt className="tech-label">{t.quizzes.yourAnswer}</dt>
                        <dd className="mt-1.5 text-sm text-ink-secondary">
                          {given.length === 0 ? (
                            <span className="text-ink-muted">{t.quizzes.notAnswered}</span>
                          ) : answer.type === 'fill_command' ? (
                            given.map((g) => (
                              <code
                                key={g}
                                className={cn(
                                  'quiz-code',
                                  answer.is_correct ? 'quiz-code-good' : 'quiz-code-bad',
                                )}
                              >
                                {g}
                              </code>
                            ))
                          ) : (
                            given.map((id) => optionText(answer.question_id, id)).join(', ')
                          )}
                        </dd>
                      </div>

                      {!answer.is_correct && (
                        <div>
                          <dt className="tech-label">{t.quizzes.correctAnswer}</dt>
                          <dd className="mt-1.5 text-sm text-ink-secondary">
                            {answer.type === 'fill_command'
                              ? answer.correct.map((c) => (
                                  <code key={c} className="quiz-code quiz-code-good">
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
                  )}

                  {answer.explanation && (
                    <p className="mt-4 border-t border-line pt-3 text-sm text-ink-secondary">
                      {answer.explanation}
                    </p>
                  )}
                </CardContent>
              </Card>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
