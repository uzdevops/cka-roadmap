'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

import { useI18n } from '@/i18n/provider';
import { listTracks } from '@/lib/tracks-api';
import type { Track } from '@/lib/types';
import { cn } from '@/lib/utils';
import { isTrack, stripTrack, TRACK_SECTIONS } from '@/tracks/config';

/**
 * Which programme of study the rail is showing.
 *
 * Only lists tracks this account may open - the API decides that, so the
 * switcher can never offer a choice that would then be refused with a 403.
 *
 * Switching keeps you on the same SECTION where one exists: from
 * /en/cka/lessons the Docker entry goes to /en/docker/lessons, not back to a
 * dashboard. Somebody comparing two tracks' lessons should not have to navigate
 * back in twice.
 */
export function TrackSwitcher() {
  const { t, locale, track: active } = useI18n();
  const pathname = usePathname() ?? '';
  const [tracks, setTracks] = useState<Track[] | null>(null);
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    listTracks(controller.signal)
      .then(setTracks)
      .catch(() => setTracks([]));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!open) return;
    const onAway = (event: MouseEvent) => {
      if (!box.current?.contains(event.target as Node)) setOpen(false);
    };
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onAway);
    document.addEventListener('keydown', onEscape);
    return () => {
      document.removeEventListener('mousedown', onAway);
      document.removeEventListener('keydown', onEscape);
    };
  }, [open]);

  // The section currently being looked at, so switching lands on its twin.
  const section = (() => {
    const rest = stripTrack(pathname.replace(`/${locale}`, '') || '/');
    const first = rest.split('/')[1] ?? '';
    return (TRACK_SECTIONS as readonly string[]).includes(first) ? first : 'dashboard';
  })();

  const current = tracks?.find((entry) => entry.slug === active) ?? null;

  const statusLabel = (entry: Track): string => {
    const e = entry.enrollment;
    if (!e || e.status === 'not_started') return t.tracks.notStarted;
    if (e.status === 'completed') return t.tracks.done;
    return `${e.current_week ?? 1}/${e.duration_weeks}`;
  };

  return (
    <div className="trk-switch" ref={box}>
      <button
        type="button"
        className="trk-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span aria-hidden className="trk-mark">
          {current?.mark || (current?.short_title ?? active).slice(0, 2).toUpperCase()}
        </span>
        <span className="trk-trigger-text">
          <span className="trk-trigger-label">{t.tracks.label}</span>
          <span className="trk-trigger-name">
            {current?.short_title ?? current?.title ?? active}
          </span>
        </span>
        <span aria-hidden className="trk-caret">
          ▾
        </span>
      </button>

      {open && (
        <div className="trk-menu" role="listbox" aria-label={t.tracks.label}>
          {tracks === null && <p className="trk-empty">{t.common.loading}</p>}
          {tracks?.length === 0 && <p className="trk-empty">{t.tracks.none}</p>}

          {tracks?.map((entry) => {
            const isCurrent = entry.slug === active;
            return (
              <Link
                key={entry.slug}
                href={`/${locale}/${entry.slug}/${section}`}
                role="option"
                aria-selected={isCurrent}
                className={cn('trk-item', isCurrent && 'trk-item-current')}
                onClick={() => setOpen(false)}
              >
                <span aria-hidden className="trk-item-mark">
                  {entry.mark || entry.short_title.slice(0, 2).toUpperCase()}
                </span>
                <span className="trk-item-body">
                  <span className="trk-item-name">{entry.short_title || entry.title}</span>
                  {/* Both categories are shown because several tracks are
                      genuinely both, and which one you are here for changes
                      what you expect to find. */}
                  <span className="trk-item-kind">
                    {[
                      entry.is_topic ? t.tracks.topic : null,
                      entry.is_certificate ? t.tracks.certificate : null,
                    ]
                      .filter(Boolean)
                      .join(' · ')}
                  </span>
                </span>
                <span
                  className={cn(
                    'trk-item-status',
                    entry.enrollment?.is_overdue && 'trk-item-late',
                  )}
                >
                  {statusLabel(entry)}
                </span>
              </Link>
            );
          })}

          <Link href={`/${locale}/tracks`} className="trk-all" onClick={() => setOpen(false)}>
            {t.tracks.seeAll}
          </Link>
        </div>
      )}
    </div>
  );
}

export { isTrack };
