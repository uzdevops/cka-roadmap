'use client';

import { useEffect, useRef, useState } from 'react';

import { useI18n } from '@/i18n/provider';

/**
 * A YouTube link, reduced to the only two things this component trusts: the
 * video id and a start offset. Nothing the admin typed reaches an attribute -
 * both URLs below are rebuilt from the parsed id.
 */
export interface YouTubeVideo {
  id: string;
  /** Start offset in seconds; 0 when the link carried none. */
  start: number;
  /** Privacy-mode player URL, safe to hand to an iframe `src`. */
  embedUrl: string;
  /** Canonical watch URL, for people who would rather open YouTube itself. */
  watchUrl: string;
}

/** Hosts that can carry a video id, after `www.` / `m.` / `music.` is stripped. */
const HOSTS = new Set(['youtube.com', 'youtu.be', 'youtube-nocookie.com']);

/** Path prefixes that put the id in the next segment. */
const ID_IN_PATH = new Set(['embed', 'shorts', 'live', 'v']);

/**
 * The id charset YouTube uses. Anchored, so anything that could change the
 * meaning of the URL we build - a slash, a dot, a quote - fails the test and
 * the whole link is rejected rather than sanitised.
 */
const ID = /^[A-Za-z0-9_-]{6,20}$/;

/**
 * `/embed/videoseries` is a playlist, not a video: it needs a `list=` the
 * player here does not carry, and would load an empty frame.
 */
const NOT_A_VIDEO = new Set(['videoseries']);

/** `90`, `90s`, `1m30s`, `2h5m1s` - the shapes a share link actually uses. */
const CLOCK = /^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$/;

const DAY_SECONDS = 86_400;

function parseStart(raw: string | null): number {
  if (!raw) return 0;
  const value = raw.trim().toLowerCase();
  if (!value) return 0;

  const seconds = /^\d+$/.test(value)
    ? Number(value)
    : (() => {
        const match = CLOCK.exec(value);
        if (!match || !match.slice(1).some(Boolean)) return NaN;
        const [, h, m, s] = match;
        return Number(h ?? 0) * 3600 + Number(m ?? 0) * 60 + Number(s ?? 0);
      })();

  if (!Number.isFinite(seconds) || seconds <= 0) return 0;
  return Math.min(Math.trunc(seconds), DAY_SECONDS);
}

/**
 * Reads a pasted YouTube link.
 *
 * Accepts `watch?v=`, `youtu.be/`, `/embed/`, `/shorts/` and `/live/`, on
 * youtube.com, youtu.be or youtube-nocookie.com, with or without `www.`, a
 * scheme, or a `&t=90s` start time. Returns null for everything else - a link
 * we cannot read is rendered as no player at all, never as a broken frame.
 */
export function parseYouTubeUrl(input: string | null | undefined): YouTubeVideo | null {
  if (!input) return null;
  const raw = input.trim();
  if (!raw) return null;

  let url: URL;
  try {
    // People paste `youtu.be/xyz` without a scheme. Anything that already
    // declares one keeps it, so a non-http scheme still fails the check below.
    url = new URL(/^[a-z][a-z0-9+.-]*:\/\//i.test(raw) ? raw : `https://${raw}`);
  } catch {
    return null;
  }

  if (url.protocol !== 'https:' && url.protocol !== 'http:') return null;

  const host = url.hostname.toLowerCase().replace(/^(?:www|m|music)\./, '');
  if (!HOSTS.has(host)) return null;

  const segments = url.pathname.split('/').filter(Boolean);

  let id: string | null = null;
  if (host === 'youtu.be') {
    id = segments[0] ?? null;
  } else if (segments.length > 0 && ID_IN_PATH.has(segments[0])) {
    id = segments[1] ?? null;
  } else if (segments.length === 0 || segments[0] === 'watch') {
    id = url.searchParams.get('v');
  }

  if (!id || !ID.test(id) || NOT_A_VIDEO.has(id)) return null;

  const start = parseStart(
    url.searchParams.get('t') ??
      url.searchParams.get('start') ??
      (url.hash.startsWith('#t=') ? url.hash.slice(3) : null),
  );

  // Built from the validated id, never from the pasted string.
  const params = new URLSearchParams({ rel: '0', playsinline: '1' });
  if (start > 0) params.set('start', String(start));

  return {
    id,
    start,
    embedUrl: `https://www.youtube-nocookie.com/embed/${id}?${params.toString()}`,
    watchUrl: `https://www.youtube.com/watch?v=${id}${start > 0 ? `&t=${start}s` : ''}`,
  };
}

/**
 * The lesson's video, above the prose.
 *
 * A click-to-load poster rather than an eager iframe: an embedded player is
 * roughly half a megabyte of third-party JavaScript, and most readers of a
 * written lesson never press play. Until they do, this is a button and some
 * text - no YouTube request, no cookie, nothing to consent to. The frame that
 * replaces it is the nocookie player and does not autoplay, so the reader
 * stays the one who decides when the video starts.
 */
export function LessonVideo({ url, title }: { url?: string | null; title: string }) {
  const { t, fill } = useI18n();
  const [active, setActive] = useState(false);
  const frame = useRef<HTMLIFrameElement>(null);

  // The poster the keyboard was on has just been replaced, so focus follows
  // into the player instead of falling back to the top of the document.
  useEffect(() => {
    if (active) frame.current?.focus();
  }, [active]);

  const video = parseYouTubeUrl(url);
  if (!video) return null;

  return (
    <figure className="vid-figure">
      <div className="vid-stage">
        {active ? (
          <iframe
            ref={frame}
            className="vid-frame"
            src={video.embedUrl}
            title={title}
            loading="lazy"
            referrerPolicy="strict-origin-when-cross-origin"
            allow="encrypted-media; picture-in-picture; fullscreen"
            allowFullScreen
          />
        ) : (
          <button
            type="button"
            className="vid-poster"
            aria-label={fill(t.lessons.videoPlay, { title })}
            onClick={() => setActive(true)}
          >
            <span aria-hidden className="vid-play">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" focusable="false">
                <path d="M8.4 5.1 19 12 8.4 18.9z" />
              </svg>
            </span>
            {/* Visible wording is the opening of the accessible name above, so
                voice control can act on what it reads (WCAG 2.5.3). */}
            <span className="vid-poster-label">{t.lessons.videoPlayShort}</span>
            <span className="vid-poster-note">{t.lessons.videoPrivacy}</span>
          </button>
        )}
      </div>

      <figcaption className="vid-caption">
        <span className="vid-caption-kind">
          <span aria-hidden className="vid-caption-glyph">
            ▶
          </span>
          <span className="tech-label">{t.lessons.videoLabel}</span>
          {active && <span className="vid-caption-note">{t.lessons.videoLoadedNote}</span>}
        </span>

        <a
          href={video.watchUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="vid-external"
        >
          {t.lessons.videoOpenExternal}
          <span aria-hidden className="lsnd-ref-arrow">
            ↗
          </span>
          <span className="sr-only"> ({t.resources.newTab})</span>
        </a>
      </figcaption>
    </figure>
  );
}
