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

import {
  ClockIcon,
  DifficultyPill,
  SectionHeading,
  TerminalBar,
} from '../_components/lab-chrome';

export default function LabPage({ params }: { params: { slug: string } }) {
  const { user, loading: authLoading } = useAuth();
  const { t, href, locale } = useI18n();
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
      .catch(
        (err) =>
          !cancelled && setError(err instanceof Error ? err.message : t.common.apiUnavailable),
      );
    return () => {
      cancelled = true;
    };
  }, [params.slug, authLoading, locale, t]);

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
        <Card className="max-w-prose overflow-hidden">
          <TerminalBar path={`~/labs/${params.slug}`} />
          <CardContent className="p-5">
            <h1 className="font-semibold text-ink">{t.labs.cannotOpen}</h1>
            <p className="mt-2 text-sm text-ink-secondary">{error}</p>
            <Link href={href('/labs')} className="mt-4 inline-block text-sm text-accent">
              {t.labs.backToLabs}
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!lab) {
    return <p className="tech-label py-16 text-center">{t.common.loading}</p>;
  }

  const difficulty =
    t.labs.difficulty[lab.difficulty as keyof typeof t.labs.difficulty] ?? lab.difficulty;

  return (
    <div className="py-4">
      <Link href={href('/labs')} className="tech-label hover:text-ink">
        {t.labs.backToLabs}
      </Link>

      {/* Hero: the same terminal window as the card it was opened from. */}
      <header className="panel-glass mt-3 max-w-4xl overflow-hidden rounded-card">
        <TerminalBar path={`~/labs/${lab.slug}`}>
          <DifficultyPill difficulty={lab.difficulty} label={difficulty} />
        </TerminalBar>

        <div className="p-5 sm:p-6">
          <h1 className="text-[28px] font-bold tracking-[-0.02em] text-ink">{lab.title}</h1>
          <p className="mt-2 max-w-prose text-ink-secondary">{lab.description}</p>

          <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2">
            <span className="tech-label inline-flex items-center gap-1.5">
              <ClockIcon />
              {formatMinutes(lab.estimated_minutes, t.common.minutes)}
            </span>
            <span className="tech-label" aria-hidden>
              ·
            </span>
            <span className="tech-label">
              {lab.tasks.length} {t.common.tasks}
            </span>
            {status !== 'not_started' && (
              <Badge variant={status === 'completed' ? 'good' : 'accent'}>
                {t.labs.status[status]}
              </Badge>
            )}
          </div>

          {user && (
            <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-line pt-4">
              <span className="tech-label">{t.labs.yourProgress}</span>
              {(['not_started', 'in_progress', 'completed'] as LabStatus[]).map((option) => (
                <Button
                  key={option}
                  size="sm"
                  variant={status === option ? 'primary' : 'outline'}
                  aria-pressed={status === option}
                  onClick={() => updateStatus(option)}
                >
                  {t.labs.status[option]}
                </Button>
              ))}
              {error && (
                <span role="alert" className="text-sm text-critical">
                  {error}
                </span>
              )}
            </div>
          )}
        </div>
      </header>

      {lab.scenario && (
        <section className="mt-10 max-w-prose">
          <SectionHeading>{t.labs.scenario}</SectionHeading>
          <div className="mt-3 whitespace-pre-line text-ink-secondary">{lab.scenario}</div>
        </section>
      )}

      {lab.environment_setup && (
        <section className="mt-10 max-w-4xl">
          <SectionHeading>{t.labs.setup}</SectionHeading>
          <p className="mt-2 max-w-prose text-sm text-ink-secondary">{t.labs.setupNote}</p>
          <div className="mt-3">
            <CodeBlock code={lab.environment_setup} />
          </div>
        </section>
      )}

      <section className="mt-12 max-w-4xl">
        <SectionHeading>{t.labs.tasksHeading}</SectionHeading>

        {/* A numbered rail: 01, 02, 03 down the left, joined by a thin line so
            the tasks read as one run rather than four loose cards. */}
        <ol className="lab-tasks mt-5">
          {lab.tasks.map((task, index) => (
            <li key={task.title} className="lab-task">
              <div className="lab-rail" aria-hidden>
                <span className="lab-num">{String(index + 1).padStart(2, '0')}</span>
                {index < lab.tasks.length - 1 && <span className="lab-rail-line" />}
              </div>

              <Card className="mb-4 min-w-0 flex-1">
                <CardContent className="p-5">
                  <h3 className="font-semibold text-ink">{task.title}</h3>
                  <p className="mt-2 max-w-prose whitespace-pre-line text-sm leading-relaxed text-ink-secondary">
                    {task.instructions}
                  </p>

                  {task.solution && (
                    <div className="mt-4">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => toggleSolution(index)}
                        aria-expanded={revealed.has(index)}
                        aria-controls={
                          revealed.has(index) ? `lab-solution-${index}` : undefined
                        }
                      >
                        {revealed.has(index) ? t.labs.hide : t.labs.reveal}
                      </Button>
                      {revealed.has(index) && (
                        <div id={`lab-solution-${index}`} className="mt-3">
                          <CodeBlock code={task.solution} />
                        </div>
                      )}
                    </div>
                  )}

                  {task.verification && (
                    <div className="mt-4">
                      <p className="tech-label">{t.labs.verify}</p>
                      <div className="mt-2">
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
        <section className="mt-12 max-w-4xl">
          <SectionHeading>{t.labs.cleanup}</SectionHeading>
          <div className="mt-3">
            <CodeBlock code={lab.cleanup} />
          </div>
        </section>
      )}

      <Card className="mt-12 max-w-prose border-dashed">
        <CardContent className="p-5">
          <h2 className="text-sm font-semibold text-ink">{t.labs.v2Heading}</h2>
          <p className="mt-2 text-sm leading-relaxed text-ink-secondary">{t.labs.v2Body}</p>
        </CardContent>
      </Card>
    </div>
  );
}
