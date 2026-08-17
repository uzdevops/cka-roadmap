'use client';

import { Meter } from '@/components/ui/meter';
import { useI18n } from '@/i18n/provider';
import type { ExamReadiness } from '@/lib/types';

/**
 * The dashboard's single hero figure: exam readiness, quiz averages weighted by
 * the real CKA domain percentages. The breakdown below is a table rather than a
 * second chart - four rows of numbers do not need marks.
 */
export function ReadinessPanel({ readiness }: { readiness: ExamReadiness }) {
  const { t } = useI18n();
  const tone =
    readiness.score >= 85
      ? 'var(--good-text)'
      : readiness.score >= 70
        ? 'var(--text-primary)'
        : readiness.score >= 40
          ? 'var(--text-primary)'
          : 'var(--text-secondary)';

  return (
    <div>
      <div className="flex flex-wrap items-end gap-x-6 gap-y-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">
            {t.dashboard.readiness}
          </p>
          <p
            className="mt-1 text-6xl font-semibold leading-none tracking-tight"
            style={{ color: tone }}
          >
            {readiness.score.toFixed(0)}
            <span className="ml-1 text-2xl font-medium text-ink-muted">%</span>
          </p>
        </div>
        <p className="mb-1 max-w-xs text-sm text-ink-secondary">{readiness.verdict}</p>
      </div>

      <div className="mt-5">
        <Meter value={readiness.score} label={t.dashboard.readiness} height={10} />
      </div>

      {readiness.breakdown.length > 0 ? (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-sm">
            <caption className="mb-2 text-left text-xs text-ink-muted">
              {t.dashboard.readinessCaption}
            </caption>
            <thead>
              <tr className="border-b border-axis text-left text-xs uppercase tracking-wide text-ink-muted">
                <th className="py-2 pr-3 font-medium">{t.dashboard.colDomain}</th>
                <th className="py-2 pr-3 text-right font-medium">{t.dashboard.colWeight}</th>
                <th className="py-2 pr-3 text-right font-medium">{t.dashboard.colQuizAvg}</th>
                <th className="py-2 text-right font-medium">{t.dashboard.colContributes}</th>
              </tr>
            </thead>
            <tbody>
              {readiness.breakdown.map((row) => (
                <tr key={row.domain} className="border-b border-line">
                  <td className="py-2 pr-3 text-ink">{row.domain}</td>
                  <td className="py-2 pr-3 text-right tabular-nums text-ink-secondary">
                    {row.weight}%
                  </td>
                  <td className="py-2 pr-3 text-right tabular-nums text-ink-secondary">
                    {row.score === null ? t.dashboard.notAttempted : `${row.score}%`}
                  </td>
                  <td className="py-2 text-right tabular-nums text-ink-secondary">
                    {row.contribution.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="mt-6 text-sm text-ink-muted">{t.dashboard.readinessEmpty}</p>
      )}
    </div>
  );
}
