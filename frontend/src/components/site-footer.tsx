'use client';

import Link from 'next/link';

import { useI18n } from '@/i18n/provider';

export function SiteFooter() {
  const { t, href } = useI18n();

  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-1 px-4 py-6 text-sm text-ink-muted sm:flex-row sm:items-center sm:justify-between">
        <p>{t.footer.tagline}</p>
        <Link href={href('/resources')} className="text-[var(--accent)] hover:underline">
          {t.footer.references}
        </Link>
        <p>{t.footer.disclaimer}</p>
      </div>
    </footer>
  );
}
