'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { LessonDetail } from '@/lib/types';

export function LessonCompleteButton({ slug }: { slug: string }) {
  const { user, loading } = useAuth();
  const { t, href, fill } = useI18n();
  const [completed, setCompleted] = useState(false);
  const [streak, setStreak] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    void apiFetch<LessonDetail>(`/lessons/${slug}`)
      .then((lesson) => !cancelled && setCompleted(lesson.completed))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [user, slug]);

  if (loading) return null;

  if (!user) {
    return (
      <div className="rounded-card border border-line bg-surface p-5">
        <p className="text-sm text-ink-secondary">
          <Link
            href={href(`/login?next=/lessons/${slug}`)}
            className="text-[var(--accent)] hover:underline"
          >
            {t.lessons.signInLink}
          </Link>{' '}
          {t.lessons.signInPrompt}
        </p>
      </div>
    );
  }

  const toggle = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await apiFetch<{ completed: boolean; streak: number }>(
        `/lessons/${slug}/complete`,
        { method: completed ? 'DELETE' : 'POST' },
      );
      setCompleted(result.completed);
      setStreak(result.streak);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.lessons.saveError);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-card border border-line bg-surface p-5">
      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={toggle} disabled={busy} variant={completed ? 'secondary' : 'primary'}>
          {completed ? t.lessons.completed : t.lessons.markComplete}
        </Button>
        {completed && streak !== null && (
          <span className="text-sm text-ink-secondary">
            {t.lessons.streak}{' '}
            <strong className="text-ink">
              {fill(streak === 1 ? t.lessons.streakDay : t.lessons.streakDays, {
                count: streak,
              })}
            </strong>
          </span>
        )}
      </div>
      {error && (
        <p role="alert" className="mt-3 text-sm text-[var(--critical)]">
          {error}
        </p>
      )}
    </div>
  );
}
