'use client';

import Link from 'next/link';

import { useI18n } from '@/i18n/provider';

export default function LocaleNotFound() {
  const { t, href } = useI18n();

  return (
    <div className="py-24 text-center">
      <p className="text-sm font-medium uppercase tracking-wide text-ink-muted">404</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-ink">
        {t.notFound.heading}
      </h1>
      <p className="mx-auto mt-3 max-w-md text-ink-secondary">{t.notFound.body}</p>
      <div className="mt-8 flex justify-center gap-3">
        <Link
          href={href('/roadmap')}
          className="inline-flex h-10 items-center rounded-lg px-4 text-sm font-medium text-[var(--accent-ink)]"
          style={{ background: 'var(--accent)' }}
        >
          {t.notFound.toRoadmap}
        </Link>
        <Link
          href={href('/')}
          className="inline-flex h-10 items-center rounded-lg border border-line px-4 text-sm font-medium text-ink"
        >
          {t.notFound.home}
        </Link>
      </div>
    </div>
  );
}
