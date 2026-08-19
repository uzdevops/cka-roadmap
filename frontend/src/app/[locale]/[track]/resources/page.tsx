import type { Metadata } from 'next';

import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { getDictionary } from '@/i18n';
import { LOCALES, normalizeLocale } from '@/i18n/config';
import { serverFetch } from '@/lib/server-api';
import type { Track } from '@/lib/types';
import { normalizeTrack } from '@/tracks/config';

// The reference list is a database column now, so it cannot be prerendered.
export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: { locale: string; track: string };
}): Promise<Metadata> {
  const locale = normalizeLocale(params.locale);
  const t = getDictionary(locale);
  return {
    title: t.meta.resourcesTitle,
    description: t.meta.resourcesDescription,
    alternates: {
      canonical: `/${locale}/${params.track}/resources`,
      languages: Object.fromEntries(
        LOCALES.map((l) => [l, `/${l}/${params.track}/resources`]),
      ),
    },
  };
}

/** "https://www.cncf.io/certification/cka/" -> "cncf.io" */
function displayHost(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    // An admin can type anything into this field; a bad URL should cost the
    // host line, not the page.
    return url;
  }
}

/**
 * The official sources for THIS track.
 *
 * They used to be four CKA links hardcoded here, which was right when there was
 * one certification and wrong the moment there were fifteen - a Docker student
 * was being handed the Kubernetes candidate handbook. They live on the track row
 * now and are edited in the admin panel.
 */
export default async function ResourcesPage({
  params,
}: {
  params: { locale: string; track: string };
}) {
  const locale = normalizeLocale(params.locale);
  const track = normalizeTrack(params.track);
  const t = getDictionary(locale);

  const tracks = await serverFetch<Track[]>('/tracks', locale, track);
  const current = tracks?.find((entry) => entry.slug === track) ?? null;
  const references = current?.references ?? [];

  return (
    <div className="py-4">
      <header className="max-w-3xl">
        <h1 className="text-[28px] font-bold tracking-[-0.02em] text-ink">
          {current?.title ?? t.resources.heading}
        </h1>
        <p className="mt-2 text-ink-secondary">
          {current?.summary || t.resources.intro}
        </p>
      </header>

      {/* Exam facts only make sense for a track that HAS an exam. A topic track
          has no pass mark and no candidate handbook, and inventing them would
          be worse than saying nothing. */}
      {current?.is_certificate && (current.exam_code || current.exam_minutes) && (
        <div className="callout callout-exam-tip mt-8 max-w-3xl">
          <span className="callout-label">{t.resources.noteLabel}</span>
          <p className="text-sm text-ink-secondary">
            {[
              current.exam_code,
              current.exam_minutes ? `${current.exam_minutes} min` : null,
              current.provider,
            ]
              .filter(Boolean)
              .join(' · ')}
          </p>
        </div>
      )}

      <section className="mt-10">
        <h2 className="text-xl font-semibold tracking-tight text-ink">
          {t.resources.linksHeading}
        </h2>

        {references.length === 0 ? (
          <p className="mt-4 max-w-3xl text-sm text-ink-secondary">
            {t.resources.empty}
          </p>
        ) : (
          /* Rows, not cards: a short list reads faster as one scannable column,
             and the glyph chip gives the eye a fixed left edge to run down. */
          <Card className="mt-5 max-w-3xl overflow-hidden">
            <ul className="divide-y divide-[var(--border)]">
              {references.map((reference) => (
                <li key={reference.url}>
                  <a
                    href={reference.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="res-row"
                  >
                    <span aria-hidden className="res-glyph">
                      {'{↗}'}
                    </span>

                    <div className="res-body">
                      <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5">
                        <h3 className="text-[15px] font-semibold tracking-[-0.01em] text-ink">
                          {reference.title}
                        </h3>
                        <Badge variant="accent">{t.resources.docsBadge}</Badge>
                      </div>

                      <p className="mt-1 font-mono text-xs text-ink-muted">
                        {displayHost(reference.url)}
                      </p>
                    </div>

                    <span aria-hidden className="res-arrow">
                      ↗
                    </span>
                    <span className="sr-only"> ({t.resources.newTab})</span>
                  </a>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </section>
    </div>
  );
}
