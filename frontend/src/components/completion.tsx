'use client';

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { apiFetch } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { LessonSummary } from '@/lib/types';

/**
 * Fetches the signed-in user's completed lessons once and shares the set, so a
 * server-rendered roadmap page can be decorated with progress without turning
 * the whole tree into a client component or firing a request per lesson.
 */
const CompletedContext = createContext<{ slugs: Set<string>; loaded: boolean }>({
  slugs: new Set(),
  loaded: false,
});

export function CompletionProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [slugs, setSlugs] = useState<Set<string>>(new Set());
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!user) {
      setSlugs(new Set());
      setLoaded(false);
      return;
    }
    let cancelled = false;
    void apiFetch<LessonSummary[]>('/lessons')
      .then((lessons) => {
        if (cancelled) return;
        setSlugs(new Set(lessons.filter((l) => l.completed).map((l) => l.slug)));
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
    return () => {
      cancelled = true;
    };
  }, [user]);

  const value = useMemo(() => ({ slugs, loaded }), [slugs, loaded]);
  return <CompletedContext.Provider value={value}>{children}</CompletedContext.Provider>;
}

export function useCompleted() {
  return useContext(CompletedContext);
}

/** A check that only appears once the lesson is actually complete. */
export function CompletionDot({ slug }: { slug: string }) {
  const { slugs } = useCompleted();
  const done = slugs.has(slug);

  return (
    <span
      aria-label={done ? 'Completed' : 'Not started'}
      title={done ? 'Completed' : 'Not started'}
      className="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full border text-[10px] leading-none"
      style={{
        borderColor: done ? 'var(--good)' : 'var(--axis)',
        background: done ? 'var(--good)' : 'transparent',
        color: 'var(--accent-ink)',
      }}
    >
      {done ? '✓' : ''}
    </span>
  );
}

/** Per-week "3 / 5" counter that fills in client-side. */
export function WeekProgress({ slugs: lessonSlugs }: { slugs: string[] }) {
  const { slugs, loaded } = useCompleted();
  if (!loaded || lessonSlugs.length === 0) return null;
  const done = lessonSlugs.filter((slug) => slugs.has(slug)).length;
  return (
    <span className="shrink-0 text-xs tabular-nums text-ink-muted">
      {done} / {lessonSlugs.length}
    </span>
  );
}
