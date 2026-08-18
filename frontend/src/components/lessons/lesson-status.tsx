'use client';

import { useCompleted } from '@/components/completion';
import { useI18n } from '@/i18n/provider';

/**
 * What the icon on the left of a lesson card says.
 *
 * `done`    - finished, either per the server render or the client refresh
 * `current` - the first lesson you can open and have not finished
 * `locked`  - its phase is gated (see the lessons page for the rule)
 * `todo`    - everything else
 */
export type LessonState = 'done' | 'current' | 'locked' | 'todo';

/**
 * A padlock. NavIcon has no lock glyph and nav-icons.tsx is not ours to edit,
 * so it lives here. `currentColor` lets `.lsn-status` set the tone.
 */
function LockGlyph() {
  return (
    <svg
      viewBox="0 0 16 16"
      width="13"
      height="13"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      focusable="false"
    >
      <rect x="3.25" y="7" width="9.5" height="6.75" rx="2" />
      <path d="M5.75 7V5.25a2.25 2.25 0 0 1 4.5 0V7" />
    </svg>
  );
}

export function LessonStatus({
  slug,
  completed,
  state,
}: {
  slug: string;
  completed: boolean;
  state: LessonState;
}) {
  const { t } = useI18n();
  const { slugs, loaded } = useCompleted();

  // The server render already carries the signed-in user's progress; the
  // provider refreshes it in the background, so prefer it once it has landed.
  const done = loaded ? slugs.has(slug) : completed;
  const resolved: LessonState = state === 'locked' ? 'locked' : done ? 'done' : state;

  // Locked cards print the reason as text, so the icon would only repeat it.
  if (resolved === 'locked') {
    return (
      <span aria-hidden className="lsn-status">
        <LockGlyph />
      </span>
    );
  }

  const label =
    resolved === 'done'
      ? t.labs.status.completed
      : resolved === 'current'
        ? t.labs.status.in_progress
        : t.labs.status.not_started;

  return (
    <span className="lsn-status" role="img" aria-label={label} title={label}>
      {resolved === 'done' ? (
        <span aria-hidden className="lsn-check">
          ✓
        </span>
      ) : resolved === 'current' ? (
        <span aria-hidden className="badge-live-dot" />
      ) : (
        <span aria-hidden className="lsn-ring" />
      )}
    </span>
  );
}
