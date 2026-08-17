'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { QuizRunner } from '@/components/quiz-runner';
import { Card, CardContent } from '@/components/ui/card';
import { useI18n } from '@/i18n/provider';
import { apiPublic } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { QuizDetail } from '@/lib/types';

export default function QuizPage({ params }: { params: { slug: string } }) {
  const { loading: authLoading } = useAuth();
  const { t, href, locale } = useI18n();
  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    let cancelled = false;
    void apiPublic<QuizDetail>(`/quizzes/${params.slug}`)
      .then((data) => !cancelled && setQuiz(data))
      .catch((err) => !cancelled && setError(err instanceof Error ? err.message : 'Failed'));
    return () => {
      cancelled = true;
    };
  }, [params.slug, authLoading, locale]);

  if (error) {
    return (
      <div className="py-12">
        <Card>
          <CardContent className="pt-5">
            <h1 className="font-semibold text-ink">{t.quizzes.cannotOpen}</h1>
            <p className="mt-2 text-sm text-ink-secondary">{error}</p>
            <Link
              href={href('/quizzes')}
              className="mt-4 inline-block text-sm text-[var(--accent)]"
            >
              {t.quizzes.backToQuizzes}
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!quiz) {
    return <p className="py-16 text-center text-sm text-ink-muted">{t.common.loading}</p>;
  }

  return <QuizRunner quiz={quiz} />;
}
