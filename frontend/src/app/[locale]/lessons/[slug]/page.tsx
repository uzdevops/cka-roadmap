import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { LessonCompleteButton } from '@/components/lesson-complete-button';
import { MarkdownContent } from '@/components/markdown-content';
import { Badge } from '@/components/ui/badge';
import { getDictionary } from '@/i18n';
import { localePath, LOCALES, normalizeLocale } from '@/i18n/config';
import { serverFetch } from '@/lib/api';
import { renderMarkdown } from '@/lib/markdown';
import type { LessonDetail } from '@/lib/types';
import { formatMinutes } from '@/lib/utils';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: { locale: string; slug: string };
}): Promise<Metadata> {
  const locale = normalizeLocale(params.locale);
  const lesson = await serverFetch<LessonDetail>(`/lessons/${params.slug}`, locale);
  if (!lesson) return { title: 'Not found' };

  const description = lesson.summary || lesson.title;

  return {
    title: lesson.title,
    description: description.slice(0, 300),
    alternates: {
      canonical: `/${locale}/lessons/${lesson.slug}`,
      languages: Object.fromEntries(
        LOCALES.map((l) => [l, `/${l}/lessons/${lesson.slug}`]),
      ),
    },
    openGraph: {
      type: 'article',
      title: lesson.title,
      description: description.slice(0, 300),
      locale: locale === 'uz' ? 'uz_UZ' : 'en_US',
    },
  };
}

export default async function LessonPage({
  params,
}: {
  params: { locale: string; slug: string };
}) {
  const locale = normalizeLocale(params.locale);
  const t = getDictionary(locale);
  const href = (path: string) => localePath(path, locale);

  const lesson = await serverFetch<LessonDetail>(`/lessons/${params.slug}`, locale);
  if (!lesson) notFound();

  const html = await renderMarkdown(lesson.content, locale);

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'LearningResource',
    name: lesson.title,
    description: lesson.summary,
    inLanguage: locale,
    educationalLevel: 'Professional certification',
    learningResourceType: 'Lesson',
    timeRequired: `PT${lesson.estimated_minutes}M`,
    isPartOf: { '@type': 'Course', name: t.meta.roadmapTitle },
  };

  return (
    <article className="py-4">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <nav className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-ink-muted">
        <Link href={href('/roadmap')} className="hover:text-ink">
          {t.nav.roadmap}
        </Link>
        {lesson.phase_slug && (
          <>
            <span aria-hidden>/</span>
            <Link href={href(`/roadmap/${lesson.phase_slug}`)} className="hover:text-ink">
              {lesson.phase_title}
            </Link>
          </>
        )}
        {lesson.week_title && (
          <>
            <span aria-hidden>/</span>
            <span>{lesson.week_title}</span>
          </>
        )}
      </nav>

      <header className="mt-4 max-w-prose">
        <h1 className="text-3xl font-semibold tracking-tight text-ink">{lesson.title}</h1>
        {lesson.summary && <p className="mt-3 text-lg text-ink-secondary">{lesson.summary}</p>}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Badge variant="outline">
            {formatMinutes(lesson.estimated_minutes, t.common.minutes)}
          </Badge>
          {lesson.is_placeholder && <Badge variant="warning">{t.lessons.draftBadge}</Badge>}
        </div>

        {/* The body fell back to English for this locale - say so rather than
            letting the reader wonder why the language changed mid-page. */}
        {!lesson.content_translated && (
          <p className="mt-4 rounded-lg border border-line bg-[var(--surface-2)] px-4 py-3 text-sm text-ink-secondary">
            {t.lessons.notTranslated}
          </p>
        )}
      </header>

      <div className="mt-10">
        <MarkdownContent html={html} />
      </div>

      <div className="mt-12 max-w-prose">
        <LessonCompleteButton slug={lesson.slug} />
      </div>

      <nav className="mt-8 flex max-w-prose flex-col gap-3 border-t border-line pt-6 sm:flex-row sm:justify-between">
        {lesson.prev_slug ? (
          <Link
            href={href(`/lessons/${lesson.prev_slug}`)}
            className="text-sm text-ink-secondary hover:text-ink"
          >
            {t.lessons.prev}
          </Link>
        ) : (
          <span />
        )}
        {lesson.next_slug && (
          <Link
            href={href(`/lessons/${lesson.next_slug}`)}
            className="text-sm text-[var(--accent)] hover:underline sm:text-right"
          >
            {t.lessons.next}
          </Link>
        )}
      </nav>
    </article>
  );
}
