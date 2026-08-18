import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

import { LessonGate } from '@/components/lesson-gate';
import { LessonReferences } from '@/components/lesson-references';
import { LessonVideo } from '@/components/lesson-video';
import { MarkdownContent } from '@/components/markdown-content';
import { Badge } from '@/components/ui/badge';
import { getDictionary } from '@/i18n';
import { localePath, LOCALES, normalizeLocale } from '@/i18n/config';
import { serverFetch } from '@/lib/server-api';
import { renderMarkdown } from '@/lib/markdown';
import type { LessonDetail } from '@/lib/types';
import { formatMinutes } from '@/lib/utils';

export const dynamic = 'force-dynamic';

/** An opening or closing code fence, with whatever follows it on the line. */
const FENCE = /^ {0,3}(`{3,}|~{3,})(.*)$/;

/**
 * The info string of every fenced code block, in document order.
 *
 * Shiki rewrites the whole `<pre>`, so the rendered HTML no longer says which
 * language a block was highlighted as. The source markdown is the only place
 * that survives, and this page already has it, so the labels are read here and
 * matched to the rendered blocks by position on the client - which drops them
 * all rather than guessing if the two counts ever disagree.
 */
function codeFenceInfo(markdown: string): string[] {
  const infos: string[] = [];
  let open: string | null = null;

  for (const line of markdown.split('\n')) {
    const match = FENCE.exec(line);
    if (!match) continue;
    const [, run, rest] = match;

    if (open) {
      // A closing fence is the same character, at least as long, and bare.
      if (run[0] === open[0] && run.length >= open.length && rest.trim() === '') {
        open = null;
      }
      continue;
    }

    // A backtick info string may not itself contain a backtick.
    if (run[0] === '`' && rest.includes('`')) continue;

    open = run;
    infos.push(rest.trim());
  }

  return infos;
}

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
  const codeInfo = codeFenceInfo(lesson.content);

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
    <article className="mx-auto max-w-prose py-2">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <header>
        {/* Where this lesson sits in the cluster of phases and weeks. */}
        <nav
          aria-label={t.lessons.breadcrumbLabel}
          className="tech-label flex flex-wrap items-center gap-x-2 gap-y-1"
        >
          <Link href={href('/roadmap')} className="lsnd-crumb">
            {t.nav.roadmap}
          </Link>
          {lesson.phase_slug && (
            <>
              <span aria-hidden className="lsnd-crumb-sep">
                /
              </span>
              <Link href={href(`/roadmap/${lesson.phase_slug}`)} className="lsnd-crumb">
                {lesson.phase_title}
              </Link>
            </>
          )}
          {lesson.week_title && (
            <>
              <span aria-hidden className="lsnd-crumb-sep">
                /
              </span>
              <span>{lesson.week_title}</span>
            </>
          )}
        </nav>

        <h1 className="mt-3 text-[28px] font-bold leading-[1.15] tracking-[-0.02em] text-ink">
          {lesson.title}
        </h1>

        {lesson.summary && (
          <p className="mt-3 text-base leading-relaxed text-ink-secondary">{lesson.summary}</p>
        )}

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Badge variant="outline">
            {formatMinutes(lesson.estimated_minutes, t.common.minutes)}
          </Badge>
          {lesson.is_placeholder && <Badge variant="warning">{t.lessons.draftBadge}</Badge>}
        </div>

        <div aria-hidden className="lsnd-rule mt-6" />

        {/* The body fell back to English for this locale - say so rather than
            letting the reader wonder why the language changed mid-page. */}
        {!lesson.content_translated && (
          <p className="lsnd-notice mt-6 px-4 py-3 text-sm text-ink-secondary">
            {t.lessons.notTranslated}
          </p>
        )}
      </header>

      {/* Above the prose, below the header: the video is context for the
          reading, not a replacement for it. Renders nothing at all when the
          link is missing or is not one this player can read. */}
      {lesson.video_url && (
        <div className="mt-8">
          <LessonVideo url={lesson.video_url} title={lesson.title} />
        </div>
      )}

      <div className="mt-9">
        <MarkdownContent html={html} codeInfo={codeInfo} />
      </div>

      <div className="mt-10">
        <LessonReferences
          heading={t.lessons.referencesHeading}
          newTab={t.resources.newTab}
          references={lesson.references ?? []}
        />
      </div>

      <div className="mt-6">
        <LessonGate slug={lesson.slug} />
      </div>

      <nav
        aria-label={t.lessons.pagerLabel}
        className="mt-10 flex flex-col gap-3 border-t border-line pt-6 sm:flex-row sm:items-center sm:justify-between"
      >
        {lesson.prev_slug ? (
          <Link
            href={href(`/lessons/${lesson.prev_slug}`)}
            className="lsnd-pager card-hover"
          >
            {t.lessons.prev}
          </Link>
        ) : (
          <span />
        )}
        {lesson.next_slug && (
          <Link
            href={href(`/lessons/${lesson.next_slug}`)}
            className="lsnd-pager lsnd-pager-next card-hover"
          >
            {t.lessons.next}
          </Link>
        )}
      </nav>
    </article>
  );
}
