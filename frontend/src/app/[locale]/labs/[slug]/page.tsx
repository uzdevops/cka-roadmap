'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { CodeBlock } from '@/components/code-block';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useI18n } from '@/i18n/provider';
import { apiFetch, apiPublic } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { LabDetail, LabStatus } from '@/lib/types';
import { formatMinutes } from '@/lib/utils';

export default function LabPage({ params }: { params: { slug: string } }) {
  const { user, loading: authLoading } = useAuth();
  const { t, href, fill, locale } = useI18n();
  const [lab, setLab] = useState<LabDetail | null>(null);
  const [status, setStatus] = useState<LabStatus>('not_started');
  const [revealed, setRevealed] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    let cancelled = false;
    void apiPublic<LabDetail>(`/labs/${params.slug}`)
      .then((data) => {
        if (cancelled) return;
        setLab(data);
        setStatus(data.status);
      })
      .catch((err) => !cancelled && setError(err instanceof Error ? err.message : 'Failed'));
    return () => {
      cancelled = true;
    };
  }, [params.slug, authLoading, locale]);

  const updateStatus = async (next: LabStatus) => {
    if (!lab) return;
    const previous = status;
    setStatus(next);
    try {
      await apiFetch(`/labs/${lab.slug}/progress`, { method: 'PUT', body: { status: next } });
    } catch (err) {
      setStatus(previous);
      setError(err instanceof Error ? err.message : t.labs.saveError);
    }
  };

  const toggleSolution = (index: number) => {
    setRevealed((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  if (error && !lab) {
    return (
      <div className="py-12">
        <Card>
          <CardContent className="pt-5">
            <h1 className="font-semibold text-ink">{t.labs.cannotOpen}</h1>
            <p className="mt-2 text-sm text-ink-secondary">{error}</p>
            <Link href={href('/labs')} className="mt-4 inline-block text-sm text-[var(--accent)]">
              {t.labs.backToLabs}
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!lab) {
    return <p className="py-16 text-center text-sm text-ink-muted">{t.common.loading}</p>;
  }

  return (
    <div className="py-4">
      <Link href={href('/labs')} className="text-sm text-ink-muted hover:text-ink">
        {t.labs.backToLabs}
      </Link>

      <header className="mt-4 max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-tight text-ink">{lab.title}</h1>
        <p className="mt-3 text-ink-secondary">{lab.description}</p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Badge variant="outline">
            {t.labs.difficulty[lab.difficulty as keyof typeof t.labs.difficulty] ??
              lab.difficulty}
          </Badge>
          <Badge variant="outline">
            {formatMinutes(lab.estimated_minutes, t.common.minutes)}
          </Badge>
          <Badge variant="outline">
            {lab.tasks.length} {t.common.tasks}
          </Badge>
        </div>
      </header>

      {user && (
        <div className="mt-6 flex flex-wrap items-center gap-3 rounded-card border border-line bg-surface p-4">
          <span className="text-sm text-ink-secondary">{t.labs.yourProgress}</span>
          {(['not_started', 'in_progress', 'completed'] as LabStatus[]).map((option) => (
            <Button
              key={option}
              size="sm"
              variant={status === option ? 'primary' : 'outline'}
              onClick={() => updateStatus(option)}
            >
              {t.labs.status[option]}
            </Button>
          ))}
          {error && <span className="text-sm text-[var(--critical)]">{error}</span>}
        </div>
      )}

      {lab.scenario && (
        <section className="mt-10 max-w-prose">
          <h2 className="text-lg font-semibold tracking-tight text-ink">{t.labs.scenario}</h2>
          <div className="mt-3 whitespace-pre-line text-ink-secondary">{lab.scenario}</div>
        </section>
      )}

      {lab.environment_setup && (
        <section className="mt-10">
          <h2 className="text-lg font-semibold tracking-tight text-ink">{t.labs.setup}</h2>
          <p className="mt-2 max-w-prose text-sm text-ink-secondary">{t.labs.setupNote}</p>
          <div className="mt-3 max-w-3xl">
            <CodeBlock code={lab.environment_setup} />
          </div>
        </section>
      )}

      <section className="mt-12">
        <h2 className="text-lg font-semibold tracking-tight text-ink">{t.labs.tasksHeading}</h2>
        <ol className="mt-4 flex flex-col gap-5">
          {lab.tasks.map((task, index) => (
            <li key={task.title}>
              <Card>
                <CardContent className="pt-5">
                  <h3 className="font-semibold text-ink">{task.title}</h3>
                  <p className="mt-2 max-w-prose whitespace-pre-line text-sm text-ink-secondary">
                    {task.instructions}
                  </p>

                  {task.solution && (
                    <div className="mt-4">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => toggleSolution(index)}
                        aria-expanded={revealed.has(index)}
                      >
                        {revealed.has(index) ? t.labs.hide : t.labs.reveal}
                      </Button>
                      {revealed.has(index) && (
                        <div className="mt-3 max-w-3xl">
                          <CodeBlock code={task.solution} />
                        </div>
                      )}
                    </div>
                  )}

                  {task.verification && (
                    <div className="mt-4">
                      <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">
                        {t.labs.verify}
                      </p>
                      <div className="mt-2 max-w-3xl">
                        <CodeBlock code={task.verification} />
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </li>
          ))}
        </ol>
      </section>

      {lab.cleanup && (
        <section className="mt-12">
          <h2 className="text-lg font-semibold tracking-tight text-ink">{t.labs.cleanup}</h2>
          <div className="mt-3 max-w-3xl">
            <CodeBlock code={lab.cleanup} />
          </div>
        </section>
      )}

      <Card className="mt-12 max-w-prose">
        <CardContent className="pt-5">
          <h2 className="font-semibold text-ink">{t.labs.v2Heading}</h2>
          <p className="mt-2 text-sm text-ink-secondary">{t.labs.v2Body}</p>
        </CardContent>
      </Card>
    </div>
  );
}
