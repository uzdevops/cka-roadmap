'use client';

import { useCompleted } from '@/components/completion';
import { Meter } from '@/components/ui/meter';
import { useI18n } from '@/i18n/provider';

/**
 * The meter and `x/y` count in a phase header row.
 *
 * It reads the shared completion set so it can never disagree with the status
 * icons on the cards below it, and falls back to the server-rendered count
 * until that set has loaded.
 */
export function PhaseProgress({
  phase,
  slugs,
  fallbackDone,
}: {
  phase: string;
  slugs: string[];
  fallbackDone: number;
}) {
  const { t, fill } = useI18n();
  const { slugs: completed, loaded } = useCompleted();

  const total = slugs.length;
  const done = loaded ? slugs.filter((slug) => completed.has(slug)).length : fallbackDone;
  const percent = total ? Math.round((done / total) * 100) : 0;

  return (
    <>
      <div className="lsn-phase-track">
        <Meter
          value={percent}
          height={3}
          label={fill(t.dashboard.phaseBarAria, { phase, done, total })}
        />
      </div>
      <span className="font-mono text-[11px] tabular-nums text-ink-muted">
        {done}/{total}
      </span>
    </>
  );
}
