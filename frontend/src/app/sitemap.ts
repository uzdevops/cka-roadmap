import type { MetadataRoute } from 'next';

import { LOCALES } from '@/i18n/config';
import { serverFetch } from '@/lib/api';
import type { LessonSummary, PhaseSummary } from '@/lib/types';

export const dynamic = 'force-dynamic';

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

/** Every URL is listed once per locale, cross-linked with hreflang alternates. */
function entry(path: string, priority: number, changeFrequency: 'weekly' | 'monthly') {
  return LOCALES.map((locale) => ({
    url: `${siteUrl}/${locale}${path}`,
    changeFrequency,
    priority,
    alternates: {
      languages: Object.fromEntries(
        LOCALES.map((other) => [other, `${siteUrl}/${other}${path}`]),
      ),
    },
  }));
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Slugs are locale-independent, so one fetch covers every language.
  const [phases, lessons] = await Promise.all([
    serverFetch<PhaseSummary[]>('/roadmap/phases'),
    serverFetch<LessonSummary[]>('/lessons'),
  ]);

  return [
    ...entry('', 1, 'weekly'),
    ...entry('/roadmap', 0.9, 'weekly'),
    ...entry('/lessons', 0.8, 'weekly'),
    ...entry('/quizzes', 0.6, 'monthly'),
    ...entry('/labs', 0.6, 'monthly'),
    ...entry('/resources', 0.5, 'monthly'),
    ...(phases ?? []).flatMap((phase) => entry(`/roadmap/${phase.slug}`, 0.7, 'monthly')),
    ...(lessons ?? [])
      .filter((lesson) => !lesson.is_placeholder)
      .flatMap((lesson) => entry(`/lessons/${lesson.slug}`, 0.7, 'monthly')),
  ];
}
