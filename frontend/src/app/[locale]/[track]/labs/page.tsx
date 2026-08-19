'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useI18n } from '@/i18n/provider';
import { apiPublic } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { LabSummary } from '@/lib/types';
import { formatMinutes } from '@/lib/utils';

import { ClockIcon, DifficultyPill, TerminalBar } from './_components/lab-chrome';

export default function LabsPage() {
  const { loading: authLoading, user } = useAuth();
  const { t, href, fill, locale } = useI18n();
  const [labs, setLabs] = useState<LabSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    let cancelled = false;
    void apiPublic<LabSummary[]>('/labs')
      .then((data) => {
        if (cancelled) return;
        setLabs(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [authLoading, user, locale]);

  const done = labs.filter((lab) => lab.status === 'completed').length;

  return (
    <div className="py-4">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="max-w-3xl">
          {/* A path, not a sentence - it reads the same in every locale, and
              it matches the path printed on every card below. */}
          <p className="lab-path">~/labs</p>
          <h1 className="mt-1 text-[28px] font-bold tracking-[-0.02em] text-ink">
            {t.labs.heading}
          </h1>
          <p className="mt-2 text-ink-secondary">{t.labs.intro}</p>
        </div>
        {labs.length > 0 && (
          <p className="tech-label">{fill(t.labs.overviewMeta, { total: labs.length, done })}</p>
        )}
      </header>

      {loading ? (
        <p className="tech-label mt-10">{t.common.loading}</p>
      ) : labs.length === 0 ? (
        <Card className="mt-8">
          <CardContent className="pt-5 text-sm text-ink-muted">{t.labs.empty}</CardContent>
        </Card>
      ) : (
        <ul className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {labs.map((lab) => {
            const difficulty =
              t.labs.difficulty[lab.difficulty as keyof typeof t.labs.difficulty] ?? lab.difficulty;

            return (
              <li key={lab.slug}>
                <Link href={href(`/labs/${lab.slug}`)} className="block h-full">
                  <Card className="card-hover flex h-full flex-col overflow-hidden">
                    <TerminalBar path={`~/labs/${lab.slug}`}>
                      <DifficultyPill difficulty={lab.difficulty} label={difficulty} />
                    </TerminalBar>

                    <CardContent className="flex flex-1 flex-col p-4">
                      <h2 className="text-base font-semibold tracking-[-0.01em] text-ink">
                        {lab.title}
                      </h2>
                      <p className="mt-2 flex-1 text-sm leading-relaxed text-ink-secondary">
                        {lab.description}
                      </p>

                      {/* Meta row. `LabSummary` carries no task count, so the
                          estimate is the only number the API can back here. */}
                      <div className="mt-4 flex items-center justify-between gap-3 border-t border-line pt-3">
                        <span className="tech-label inline-flex items-center gap-1.5">
                          <ClockIcon />
                          {formatMinutes(lab.estimated_minutes, t.common.minutes)}
                        </span>
                        {lab.status !== 'not_started' && (
                          <Badge variant={lab.status === 'completed' ? 'good' : 'accent'}>
                            {t.labs.status[lab.status]}
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
