'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { FieldError } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import type { AdminLab } from '@/lib/types';

export default function AdminLabsPage() {
  const { t, href, fill } = useI18n();
  const [labs, setLabs] = useState<AdminLab[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void apiFetch<AdminLab[]>('/admin/labs')
      .then(setLabs)
      .catch((err) => setError(err instanceof Error ? err.message : t.admin.loadFailed));
  }, []);

  return (
    <div>
      <p className="mb-4 text-sm text-ink-secondary">
        {fill(t.admin.labsCount, { count: labs.length })}
      </p>
      <FieldError>{error}</FieldError>

      <div className="overflow-x-auto rounded-card border border-line bg-surface">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-axis text-left text-xs uppercase tracking-wide text-ink-muted">
              <th className="px-4 py-2.5 font-medium">{t.admin.colTitle}</th>
              <th className="px-4 py-2.5 font-medium">{t.admin.colSlug}</th>
              <th className="px-4 py-2.5 font-medium">{t.admin.colDifficulty}</th>
              <th className="px-4 py-2.5 text-right font-medium">{t.admin.colTasks}</th>
              <th className="px-4 py-2.5 font-medium">{t.admin.colState}</th>
              <th className="px-4 py-2.5 text-right font-medium">{t.admin.colActions}</th>
            </tr>
          </thead>
          <tbody>
            {labs.map((lab) => (
              <tr key={lab.id} className="border-b border-line last:border-0">
                <td className="px-4 py-2.5 text-ink">{lab.title}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-ink-muted">{lab.slug}</td>
                <td className="px-4 py-2.5 capitalize text-ink-secondary">{lab.difficulty}</td>
                <td className="px-4 py-2.5 text-right tabular-nums text-ink-secondary">
                  {lab.tasks.length}
                </td>
                <td className="px-4 py-2.5">
                  <Badge variant={lab.is_published ? 'good' : 'warning'}>
                    {lab.is_published ? t.common.published : t.common.hidden}
                  </Badge>
                </td>
                <td className="px-4 py-2.5 text-right">
                  <Link
                    href={href(`/admin/labs/${lab.id}`)}
                    className="text-[var(--accent)] underline decoration-[var(--accent)]/40 underline-offset-2 hover:decoration-[var(--accent)]"
                  >
                    {t.common.edit}
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
