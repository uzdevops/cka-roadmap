'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { FieldError } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import type { AdminQuiz } from '@/lib/types';

export default function AdminQuizzesPage() {
  const { t, href, fill } = useI18n();
  const [quizzes, setQuizzes] = useState<AdminQuiz[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void apiFetch<AdminQuiz[]>('/admin/quizzes')
      .then(setQuizzes)
      .catch((err) => setError(err instanceof Error ? err.message : t.admin.loadFailed));
  }, []);

  return (
    <div>
      <p className="mb-4 text-sm text-ink-secondary">
        {fill(t.admin.quizzesCount, { count: quizzes.length })}
      </p>
      <FieldError>{error}</FieldError>

      <div className="overflow-x-auto rounded-card border border-line bg-surface">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-axis text-left text-xs uppercase tracking-wide text-ink-muted">
              <th className="px-4 py-2.5 font-medium">{t.admin.colTitle}</th>
              <th className="px-4 py-2.5 font-medium">{t.admin.colSlug}</th>
              <th className="px-4 py-2.5 text-right font-medium">{t.admin.colQuestions}</th>
              <th className="px-4 py-2.5 text-right font-medium">{t.admin.colPass}</th>
              <th className="px-4 py-2.5 font-medium">{t.admin.colState}</th>
              <th className="px-4 py-2.5 text-right font-medium">{t.admin.colActions}</th>
            </tr>
          </thead>
          <tbody>
            {quizzes.map((quiz) => (
              <tr key={quiz.id} className="border-b border-line last:border-0">
                <td className="px-4 py-2.5 text-ink">{quiz.title}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-ink-muted">{quiz.slug}</td>
                <td className="px-4 py-2.5 text-right tabular-nums text-ink-secondary">
                  {quiz.questions.length}
                </td>
                <td className="px-4 py-2.5 text-right tabular-nums text-ink-secondary">
                  {quiz.pass_score}%
                </td>
                <td className="px-4 py-2.5">
                  <Badge variant={quiz.is_published ? 'good' : 'warning'}>
                    {quiz.is_published ? t.common.published : t.common.hidden}
                  </Badge>
                </td>
                <td className="px-4 py-2.5 text-right">
                  <Link
                    href={href(`/admin/quizzes/${quiz.id}`)}
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
