'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { LessonVideo, parseYouTubeUrl } from '@/components/lesson-video';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FieldError, Input, Label, Textarea } from '@/components/ui/field';
import { DEFAULT_LOCALE, LOCALES } from '@/i18n/config';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import type { AdminLesson } from '@/lib/types';
import { cn } from '@/lib/utils';

/** Locales an admin can supply overrides for: everything except the base one. */
const TRANSLATABLE = LOCALES.filter((l) => l !== DEFAULT_LOCALE);

export default function AdminLessonEditorPage({ params }: { params: { id: string } }) {
  const { t, href, fill, locale } = useI18n();

  const [lesson, setLesson] = useState<AdminLesson | null>(null);
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [minutes, setMinutes] = useState(30);
  const [published, setPublished] = useState(true);
  const [translations, setTranslations] = useState<Record<string, Record<string, string>>>({});

  const [tab, setTab] = useState<'write' | 'preview'>('write');
  const [previewHtml, setPreviewHtml] = useState('');
  const [previewing, setPreviewing] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void apiFetch<AdminLesson>(`/admin/lessons/${params.id}`)
      .then((data) => {
        setLesson(data);
        setContent(data.content);
        setTitle(data.title);
        setSummary(data.summary);
        setVideoUrl(data.video_url ?? '');
        setMinutes(data.estimated_minutes);
        setPublished(data.is_published);
        setTranslations((data.translations ?? {}) as Record<string, Record<string, string>>);
      })
      .catch((err) => setError(err instanceof Error ? err.message : t.admin.loadFailed));
  }, [params.id, t.admin.loadFailed]);

  // The link is read with the same parser the lesson page uses, so what the
  // editor calls valid is exactly what will render a player.
  const trimmedVideo = videoUrl.trim();
  const video = useMemo(() => parseYouTubeUrl(trimmedVideo), [trimmedVideo]);
  const videoInvalid = trimmedVideo !== '' && video === null;

  // Preview goes through the same server pipeline the lesson page uses, so
  // Shiki highlighting and callouts render exactly as students will see them.
  const renderPreview = useCallback(async () => {
    setPreviewing(true);
    try {
      const res = await fetch('/api/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ markdown: content, locale }),
      });
      const data = await res.json();
      setPreviewHtml(data.html);
    } finally {
      setPreviewing(false);
    }
  }, [content, locale]);

  useEffect(() => {
    if (tab !== 'preview') return;
    void renderPreview();
  }, [tab, renderPreview]);

  const setTranslationField = (locale: string, field: string, value: string) => {
    setTranslations((prev) => ({
      ...prev,
      [locale]: { ...(prev[locale] ?? {}), [field]: value },
    }));
  };

  const save = async () => {
    // Saving an unreadable link would drop the video silently on the lesson
    // page, so the editor stops here and says which shapes it can read.
    if (videoInvalid) {
      setError(t.admin.videoUrlInvalid);
      return;
    }

    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      await apiFetch(`/admin/lessons/${params.id}`, {
        method: 'PATCH',
        body: {
          title,
          summary,
          content,
          // Stored as typed; an empty box clears the video.
          video_url: trimmedVideo || null,
          estimated_minutes: minutes,
          is_published: published,
          translations,
        },
      });
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.profile.saveFailed);
    } finally {
      setBusy(false);
    }
  };

  if (error && !lesson) return <p className="text-sm text-[var(--critical)]">{error}</p>;
  if (!lesson) return <p className="text-sm text-ink-muted">{t.common.loading}</p>;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Link href={href('/admin/lessons')} className="text-sm text-ink-muted hover:text-ink">
          {t.admin.backToLessons}
        </Link>
        <div className="flex items-center gap-3">
          {saved && <span className="text-sm text-[var(--good-text)]">{t.common.saved}</span>}
          <Link
            href={href(`/lessons/${lesson.slug}`)}
            target="_blank"
            className="text-sm text-[var(--accent)] underline decoration-[var(--accent)]/40 underline-offset-2 hover:decoration-[var(--accent)]"
          >
            {t.admin.viewLive}
          </Link>
          <Button onClick={save} disabled={busy}>
            {busy ? t.common.saving : t.common.save}
          </Button>
        </div>
      </div>

      <FieldError>{error}</FieldError>

      <Card className="mb-5">
        <CardContent className="grid gap-4 pt-5 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Label htmlFor="title">{t.admin.title}</Label>
            <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <Label htmlFor="summary">{t.admin.summary}</Label>
            <Input id="summary" value={summary} onChange={(e) => setSummary(e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <Label htmlFor="video-url">{t.admin.videoUrl}</Label>
            <Input
              id="video-url"
              inputMode="url"
              spellCheck={false}
              placeholder="https://www.youtube.com/watch?v=…"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              aria-invalid={videoInvalid || undefined}
              aria-describedby={
                trimmedVideo ? 'video-url-hint video-url-state' : 'video-url-hint'
              }
              className={cn(videoInvalid && 'vid-input-invalid')}
            />
            <p id="video-url-hint" className="mt-1.5 text-xs text-ink-muted">
              {t.admin.videoUrlHint}
            </p>
            {/* State is carried by a glyph and a sentence as well as the
                colour, so it survives a monochrome or colour-blind read. */}
            {trimmedVideo !== '' && (
              <p
                id="video-url-state"
                className={cn('vid-check', videoInvalid ? 'vid-check-bad' : 'vid-check-ok')}
              >
                <span aria-hidden className="vid-check-glyph">
                  {videoInvalid ? '✕' : '✓'}
                </span>
                {videoInvalid
                  ? t.admin.videoUrlInvalid
                  : fill(t.admin.videoUrlOk, { id: video?.id ?? '' })}
              </p>
            )}
            {video && (
              <div className="vid-admin-preview">
                {/* Keyed by id, so pasting a different video hands back a
                    fresh poster instead of leaving the old frame loaded. */}
                <LessonVideo key={video.id} url={trimmedVideo} title={title || lesson.title} />
              </div>
            )}
          </div>
          <div>
            <Label htmlFor="minutes">{t.admin.estimatedMinutes}</Label>
            <Input
              id="minutes"
              type="number"
              min={5}
              value={minutes}
              onChange={(e) => setMinutes(Number(e.target.value))}
            />
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-sm text-ink-secondary">
              <input
                type="checkbox"
                className="h-4 w-4 accent-[var(--accent)]"
                checked={published}
                onChange={(e) => setPublished(e.target.checked)}
              />
              {t.admin.publishedLabel}
            </label>
          </div>
          <p className="text-xs text-ink-muted sm:col-span-2">
            {fill(t.admin.slugImmutable, { slug: lesson.slug })}
          </p>
        </CardContent>
      </Card>

      <div className="mb-3 flex gap-1 border-b border-line">
        {(['write', 'preview'] as const).map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => setTab(value)}
            className={cn(
              '-mb-px border-b-2 px-3 py-2 text-sm capitalize transition-colors',
              tab === value
                ? 'border-[var(--accent)] text-ink'
                : 'border-transparent text-ink-secondary hover:text-ink',
            )}
          >
            {value === 'write' ? t.admin.write : t.admin.preview}
          </button>
        ))}
      </div>

      {tab === 'write' ? (
        <>
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="min-h-[32rem] text-sm"
            spellCheck={false}
          />
          <p className="mt-2 text-xs text-ink-muted">{t.admin.markdownHelp}</p>
        </>
      ) : (
        <Card>
          <CardContent className="pt-6">
            {previewing ? (
              <p className="text-sm text-ink-muted">{t.admin.rendering}</p>
            ) : (
              <div
                className="prose-lesson max-w-prose"
                dangerouslySetInnerHTML={{ __html: previewHtml }}
              />
            )}
          </CardContent>
        </Card>
      )}

      {/* Per-locale overrides. Any field left blank falls back to the English
          text above, field by field. */}
      {TRANSLATABLE.map((code) => (
        <Card key={code} className="mt-6">
          <CardHeader>
            <CardTitle>{t.admin.translationHeading}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <p className="text-xs text-ink-muted">{t.admin.translationHelp}</p>
            <div>
              <Label>{t.admin.translationTitle}</Label>
              <Input
                value={translations[code]?.title ?? ''}
                onChange={(e) => setTranslationField(code, 'title', e.target.value)}
              />
            </div>
            <div>
              <Label>{t.admin.translationSummary}</Label>
              <Input
                value={translations[code]?.summary ?? ''}
                onChange={(e) => setTranslationField(code, 'summary', e.target.value)}
              />
            </div>
            <div>
              <Label>{t.admin.translationContent}</Label>
              <Textarea
                className="min-h-[24rem] text-sm"
                spellCheck={false}
                value={translations[code]?.content ?? ''}
                onChange={(e) => setTranslationField(code, 'content', e.target.value)}
              />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
