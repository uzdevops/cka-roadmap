import type { Metadata } from 'next';

import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { getDictionary } from '@/i18n';
import { LOCALES, normalizeLocale } from '@/i18n/config';

export async function generateMetadata({
  params,
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const locale = normalizeLocale(params.locale);
  const t = getDictionary(locale);
  return {
    title: t.meta.resourcesTitle,
    description: t.meta.resourcesDescription,
    alternates: {
      canonical: `/${locale}/resources`,
      languages: Object.fromEntries(LOCALES.map((l) => [l, `/${l}/resources`])),
    },
  };
}

/**
 * The glyph vocabulary for a reference row. Every reference below is a document
 * to read, so only `docs` is in play today - `video` and `practice` are named
 * here so the row shape is ready the moment a reference carries another kind.
 */
const KIND_GLYPH = {
  docs: '{K}',
  video: '{▶}',
  practice: '{⚗}',
} as const;

/**
 * URLs and their kind are locale-independent, so only the copy lives in the
 * dictionaries - `key` indexes into `t.resources.items`.
 */
const REFERENCES = [
  { key: 'official', kind: 'docs', url: 'https://www.cncf.io/certification/cka/' },
  { key: 'curriculum', kind: 'docs', url: 'https://github.com/cncf/curriculum' },
  {
    key: 'handbook',
    kind: 'docs',
    url: 'https://www.cncf.io/certification/candidate-handbook',
  },
  {
    key: 'tips',
    kind: 'docs',
    url: 'http://training.linuxfoundation.org/go//Important-Tips-CKA-CKAD',
  },
] as const;

/** "https://www.cncf.io/certification/cka/" -> "cncf.io" */
function displayHost(url: string): string {
  return new URL(url).hostname.replace(/^www\./, '');
}

export default function ResourcesPage({ params }: { params: { locale: string } }) {
  const locale = normalizeLocale(params.locale);
  const t = getDictionary(locale);

  return (
    <div className="py-4">
      <header className="max-w-3xl">
        <h1 className="text-[28px] font-bold tracking-[-0.02em] text-ink">
          {t.resources.heading}
        </h1>
        <p className="mt-2 text-ink-secondary">{t.resources.intro}</p>
      </header>

      {/* Same callout treatment the lesson Markdown uses for :::exam-tip. */}
      <div className="callout callout-exam-tip mt-8 max-w-3xl">
        <span className="callout-label">{t.resources.noteLabel}</span>
        <p className="text-sm text-ink-secondary">{t.resources.noteBody}</p>
      </div>

      <section className="mt-10">
        <h2 className="text-xl font-semibold tracking-tight text-ink">
          {t.resources.linksHeading}
        </h2>

        {/* Rows, not cards: four links read faster as one scannable list, and
            the glyph chip gives the eye a fixed left edge to run down. */}
        <Card className="mt-5 max-w-3xl overflow-hidden">
          <ul className="divide-y divide-[var(--border)]">
            {REFERENCES.map((reference) => {
              const item = t.resources.items[reference.key];
              return (
                <li key={reference.key}>
                  <a
                    href={reference.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="res-row"
                  >
                    <span aria-hidden className="res-glyph">
                      {KIND_GLYPH[reference.kind]}
                    </span>

                    <div className="res-body">
                      <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5">
                        <h3 className="text-[15px] font-semibold tracking-[-0.01em] text-ink">
                          {item.title}
                        </h3>
                        <Badge variant="accent">{t.resources.docsBadge}</Badge>
                      </div>

                      <p className="mt-1 font-mono text-xs text-ink-muted">
                        {displayHost(reference.url)}
                      </p>

                      <p className="mt-2 text-sm text-ink-secondary">{item.body}</p>
                    </div>

                    <span aria-hidden className="res-arrow">
                      ↗
                    </span>
                    <span className="sr-only"> ({t.resources.newTab})</span>
                  </a>
                </li>
              );
            })}
          </ul>
        </Card>
      </section>
    </div>
  );
}
