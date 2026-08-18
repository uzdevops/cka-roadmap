import Link from 'next/link';

import './globals.css';

import { BrandMark } from '@/components/brand-mark';
import { fill, getDictionary } from '@/i18n';
import { DEFAULT_LOCALE } from '@/i18n/config';

/**
 * Root-level 404, reached only for paths outside the `[locale]` tree. It
 * renders its own document shell because the root layout is a passthrough.
 *
 * There is no locale segment to read here and no I18nProvider above it, so it
 * takes the default dictionary directly rather than hard-coding English. That
 * also keeps the product name in one place: this page names the site, and the
 * site is renamed in the dictionaries.
 */
export default function NotFound() {
  const t = getDictionary(DEFAULT_LOCALE);

  return (
    <html lang={DEFAULT_LOCALE}>
      <body className="min-h-screen antialiased">
        <div className="mx-auto max-w-6xl px-4 py-24 text-center">
          {/* .auth-mark is inline-flex, so it is centred by the row around it
              rather than by a margin of its own. */}
          <div className="flex justify-center">
            <span aria-hidden className="auth-mark brand-tile">
              <BrandMark size={48} />
            </span>
          </div>
          <p className="mt-8 text-sm font-medium uppercase tracking-wide text-ink-muted">404</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-ink">
            {t.notFound.heading}
          </h1>
          <p className="mx-auto mt-3 max-w-md text-ink-secondary">{t.notFound.bodyRoot}</p>
          <Link
            href={`/${DEFAULT_LOCALE}`}
            className="mt-8 inline-flex h-10 items-center rounded-lg px-4 text-sm font-medium text-[var(--accent-ink)]"
            style={{ background: 'var(--accent)' }}
          >
            {fill(t.notFound.goToSite, { site: t.meta.siteName })}
          </Link>
        </div>
      </body>
    </html>
  );
}
