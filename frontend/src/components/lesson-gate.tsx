'use client';

import Link from 'next/link';
import { useCallback, useEffect, useRef, useState } from 'react';

import { QuizRunner } from '@/components/quiz-runner';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Meter } from '@/components/ui/meter';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import type { LessonDetail, QuizDetail, QuizResult } from '@/lib/types';

/**
 * What finishes a lesson.
 *
 * A lesson with a quiz is completed by scoring at least its pass mark - the API
 * records that itself when it grades the attempt, and refuses the plain
 * "mark as complete" call, so the button below can never bypass the gate. A
 * lesson without a quiz keeps the single button it always had.
 */
export function LessonGate({ slug }: { slug: string }) {
  const { t, href, fill } = useI18n();

  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [running, setRunning] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const box = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    try {
      setLesson(await apiFetch<LessonDetail>(`/lessons/${slug}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : t.lessons.saveError);
    }
  }, [slug, t.lessons.saveError]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!lesson) return null;

  // --- no quiz yet: the original button ---
  if (!lesson.quiz_slug) {
    const toggle = async () => {
      setBusy(true);
      setError(null);
      try {
        await apiFetch(`/lessons/${slug}/complete`, {
          method: lesson.completed ? 'DELETE' : 'POST',
        });
        await load();
      } catch (err) {
        setError(err instanceof Error ? err.message : t.lessons.saveError);
      } finally {
        setBusy(false);
      }
    };

    return (
      <Card className="lsnd-gate">
        <CardContent className="pt-5">
          <h2 className="tech-label">{t.lessons.quizHeading}</h2>

          <div className="mt-3 flex flex-wrap items-center gap-3">
            <Button
              variant={lesson.completed ? 'outline' : 'primary'}
              onClick={() => void toggle()}
              disabled={busy}
            >
              {lesson.completed ? t.lessons.completed : t.lessons.markComplete}
            </Button>
            <p className="text-xs text-ink-muted">{t.lessons.noQuizYet}</p>
          </div>

          {error && (
            <p role="alert" className="lsnd-error mt-3 text-sm">
              {error}
            </p>
          )}
        </CardContent>
      </Card>
    );
  }

  const pass = lesson.quiz_pass_score ?? 90;
  const best = lesson.quiz_best_score ?? 0;

  const startQuiz = async () => {
    setBusy(true);
    setError(null);
    try {
      setQuiz(await apiFetch<QuizDetail>(`/quizzes/${lesson.quiz_slug}`));
      setRunning(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.quizzes.cannotOpen);
    } finally {
      setBusy(false);
    }
  };

  const onResult = (result: QuizResult) => {
    // The server already recorded completion if this passed; re-read rather
    // than guessing, so the badge and the dashboard agree.
    void load();
    if (result.score >= pass) setRunning(false);
    // The result renders at the foot of a long lesson; without this the reader
    // is left staring at the top of the page wondering whether anything landed.
    requestAnimationFrame(() =>
      box.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
    );
  };

  if (running && quiz) {
    return (
      <div ref={box}>
        <Card className="lsnd-gate">
          <CardContent className="pt-5">
            <QuizRunner quiz={quiz} onResult={onResult} />
            <Button
              variant="ghost"
              size="sm"
              className="mt-4 -ml-3"
              onClick={() => setRunning(false)}
            >
              {t.quizzes.closeQuiz}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div ref={box}>
      <Card className="lsnd-gate">
        <CardContent className="pt-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="tech-label">{t.lessons.quizHeading}</h2>
            {lesson.completed ? (
              <Badge variant="good">{t.lessons.completed}</Badge>
            ) : (
              <Badge variant="outline">{fill(t.lessons.quizRequirement, { score: pass })}</Badge>
            )}
          </div>

          <p className="mt-3 text-sm leading-relaxed text-ink-secondary">
            {lesson.completed
              ? t.lessons.quizPassedBody
              : fill(t.lessons.quizIntro, { score: pass })}
          </p>

          {lesson.quiz_attempts > 0 && (
            <div className="mt-5 max-w-sm rounded-[10px] border border-line bg-surface-2 px-3.5 py-3">
              <div className="mb-2 flex items-baseline justify-between gap-3">
                <span className="tech-label">{t.quizzes.colScore}</span>
                <span className="font-mono text-sm font-semibold tabular-nums text-ink">
                  {best}%
                </span>
              </div>
              <Meter value={best} label={t.quizzes.colScore} />
              <p className="tech-label mt-2">
                {fill(t.quizzes.metaAttempts, { count: lesson.quiz_attempts })}
              </p>
            </div>
          )}

          <div className="mt-5 flex flex-wrap items-center gap-4">
            <Button onClick={() => void startQuiz()} disabled={busy}>
              {busy
                ? t.common.loading
                : lesson.quiz_attempts > 0
                  ? t.quizzes.retakeButton
                  : t.quizzes.start}
            </Button>
            {lesson.completed && lesson.next_slug && (
              <Link href={href(`/lessons/${lesson.next_slug}`)} className="lsnd-next-link">
                {t.lessons.next}
              </Link>
            )}
          </div>

          {error && (
            <p role="alert" className="lsnd-error mt-3 text-sm">
              {error}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
