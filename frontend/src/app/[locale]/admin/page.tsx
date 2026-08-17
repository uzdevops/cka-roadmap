'use client';

import { useEffect, useState } from 'react';

import { StatTile } from '@/components/charts/stat-tile';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import type { AdminStats } from '@/lib/types';

export default function AdminOverviewPage() {
  const { t, fill } = useI18n();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void apiFetch<AdminStats>('/admin/stats')
      .then(setStats)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed'));
  }, []);

  if (error) return <p className="text-sm text-[var(--critical)]">{error}</p>;
  if (!stats) return <p className="text-sm text-ink-muted">{t.common.loading}</p>;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatTile
        label={t.admin.stats.users}
        value={stats.users}
        hint={fill(t.admin.stats.usersHint, {
          students: stats.students,
          admins: stats.admins,
        })}
      />
      <StatTile
        label={t.admin.stats.lessons}
        value={stats.lessons}
        hint={fill(t.admin.stats.lessonsHint, {
          phases: stats.phases,
          weeks: stats.weeks,
        })}
      />
      <StatTile
        label={t.admin.stats.quizzes}
        value={stats.quizzes}
        hint={fill(t.admin.stats.quizzesHint, { count: stats.questions })}
      />
      <StatTile label={t.admin.stats.labs} value={stats.labs} />
      <StatTile label={t.admin.stats.attempts} value={stats.quiz_attempts} />
      <StatTile
        label={t.admin.stats.completed}
        value={stats.completed_lessons}
        hint={t.admin.stats.completedHint}
      />
    </div>
  );
}
