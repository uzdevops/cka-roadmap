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

  return (
    <div className="py-4">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-tight text-ink">{t.labs.heading}</h1>
        <p className="mt-3 text-ink-secondary">{t.labs.intro}</p>
      </header>

      {loading ? (
        <p className="mt-10 text-sm text-ink-muted">{t.common.loading}</p>
      ) : labs.length === 0 ? (
        <Card className="mt-8">
          <CardContent className="pt-5 text-sm text-ink-muted">{t.labs.empty}</CardContent>
        </Card>
      ) : (
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {labs.map((lab) => (
            <Link key={lab.slug} href={href(`/labs/${lab.slug}`)} className="group">
              <Card className="h-full transition-colors group-hover:border-[var(--accent)]">
                <CardContent className="flex h-full flex-col pt-5">
                  <div className="flex items-start justify-between gap-3">
                    <h2 className="font-semibold text-ink">{lab.title}</h2>
                    {lab.status !== 'not_started' && (
                      <Badge variant={lab.status === 'completed' ? 'good' : 'accent'}>
                        {t.labs.status[lab.status]}
                      </Badge>
                    )}
                  </div>
                  <p className="mt-2 flex-1 text-sm text-ink-secondary">{lab.description}</p>
                  <p className="mt-4 text-xs text-ink-muted">
                    {fill(t.roadmap.labMeta, {
                      difficulty:
                        t.labs.difficulty[lab.difficulty as keyof typeof t.labs.difficulty] ??
                        lab.difficulty,
                      minutes: formatMinutes(lab.estimated_minutes, t.common.minutes),
                    })}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
