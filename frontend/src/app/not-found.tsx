import Link from 'next/link';

import './globals.css';

import { DEFAULT_LOCALE } from '@/i18n/config';

/**
 * Root-level 404, reached only for paths outside the `[locale]` tree. It
 * renders its own document shell because the root layout is a passthrough.
 */
export default function NotFound() {
  return (
    <html lang={DEFAULT_LOCALE}>
      <body className="min-h-screen antialiased">
        <div className="mx-auto max-w-6xl px-4 py-24 text-center">
          <p className="text-sm font-medium uppercase tracking-wide text-ink-muted">404</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-ink">
            Page not found
          </h1>
          <p className="mx-auto mt-3 max-w-md text-ink-secondary">
            That page does not exist.
          </p>
          <Link
            href={`/${DEFAULT_LOCALE}`}
            className="mt-8 inline-flex h-10 items-center rounded-lg px-4 text-sm font-medium text-[var(--accent-ink)]"
            style={{ background: 'var(--accent)' }}
          >
            Go to CKA Prep
          </Link>
        </div>
      </body>
    </html>
  );
}
