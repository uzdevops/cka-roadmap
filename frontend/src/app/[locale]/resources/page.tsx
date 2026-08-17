import type { Metadata } from 'next';

import { Card, CardContent } from '@/components/ui/card';
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
 * URLs are locale-independent, so only the copy lives in the dictionaries -
 * `key` indexes into `t.resources.items`.
 */
const REFERENCES = [
  { key: 'official', url: 'https://www.cncf.io/certification/cka/' },
  { key: 'curriculum', url: 'https://github.com/cncf/curriculum' },
  { key: 'handbook', url: 'https://www.cncf.io/certification/candidate-handbook' },
  { key: 'tips', url: 'http://training.linuxfoundation.org/go//Important-Tips-CKA-CKAD' },
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
        <h1 className="text-3xl font-semibold tracking-tight text-ink">
          {t.resources.heading}
        </h1>
        <p className="mt-3 text-ink-secondary">{t.resources.intro}</p>
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

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {REFERENCES.map((reference) => {
            const item = t.resources.items[reference.key];
            return (
              <a
                key={reference.key}
                href={reference.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group"
              >
                <Card className="h-full transition-colors group-hover:border-[var(--accent)]">
                  <CardContent className="flex h-full flex-col pt-5">
                    <h3 className="flex items-start gap-1.5 font-semibold text-ink">
                      <span>{item.title}</span>
                      <span aria-hidden className="shrink-0 text-[var(--accent)]">
                        ↗
                      </span>
                      <span className="sr-only"> ({t.resources.newTab})</span>
                    </h3>
                    <p className="mt-2 flex-1 text-sm text-ink-secondary">{item.body}</p>
                    <p className="mt-4 text-xs text-ink-muted">{displayHost(reference.url)}</p>
                  </CardContent>
                </Card>
              </a>
            );
          })}
        </div>
      </section>
    </div>
  );
}
