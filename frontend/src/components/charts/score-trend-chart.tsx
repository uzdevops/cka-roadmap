'use client';

import { useMemo, useRef, useState } from 'react';

import { ViewToggle } from '@/components/charts/phase-progress-chart';
import { useI18n } from '@/i18n/provider';
import type { QuizScorePoint } from '@/lib/types';
import { formatDateLocale } from '@/lib/utils';

const W = 720;
const H = 260;
const PAD = { top: 16, right: 52, bottom: 34, left: 40 };

/**
 * Quiz scores over time. One series, so no legend box - the card title names
 * it. 2px line, >=8px end marker with a 2px surface ring, hairline solid
 * gridlines, and a crosshair tooltip instead of a label on every point.
 */
export function ScoreTrendChart({ points }: { points: QuizScorePoint[] }) {
  const { t, fill, locale } = useI18n();
  const [view, setView] = useState<'chart' | 'table'>('chart');
  const [active, setActive] = useState<number | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  const coords = useMemo(() => {
    if (points.length === 0) return [];
    const step = points.length === 1 ? 0 : plotW / (points.length - 1);
    return points.map((point, i) => ({
      x: PAD.left + (points.length === 1 ? plotW / 2 : i * step),
      y: PAD.top + plotH - (Math.max(0, Math.min(100, point.score)) / 100) * plotH,
      point,
    }));
  }, [points, plotW, plotH]);

  if (points.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-ink-muted">
        {t.dashboard.scoreChartEmpty}
      </p>
    );
  }

  const linePath = coords.map((c, i) => `${i === 0 ? 'M' : 'L'}${c.x},${c.y}`).join(' ');
  const areaPath =
    coords.length > 1
      ? `${linePath} L${coords.at(-1)!.x},${PAD.top + plotH} L${coords[0].x},${PAD.top + plotH} Z`
      : '';

  const last = coords.at(-1)!;
  const hovered = active === null ? null : coords[active];

  const onMove = (event: React.MouseEvent<SVGSVGElement>) => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * W;
    let nearest = 0;
    let best = Infinity;
    coords.forEach((c, i) => {
      const distance = Math.abs(c.x - x);
      if (distance < best) {
        best = distance;
        nearest = i;
      }
    });
    setActive(nearest);
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="text-sm text-ink-secondary">{t.dashboard.scoreChartCaption}</p>
        <ViewToggle view={view} onChange={setView} />
      </div>

      {view === 'table' ? (
        <ScoreTable points={points} />
      ) : (
        <div className="relative">
          <svg
            ref={svgRef}
            viewBox={`0 0 ${W} ${H}`}
            className="h-auto w-full touch-none"
            role="img"
            aria-label={fill(t.dashboard.scoreChartAria, { score: last.point.score })}
            onMouseMove={onMove}
            onMouseLeave={() => setActive(null)}
          >
            {/* Gridlines: solid hairlines, one step off surface. */}
            {[0, 25, 50, 75, 100].map((tick) => {
              const y = PAD.top + plotH - (tick / 100) * plotH;
              return (
                <g key={tick}>
                  <line
                    x1={PAD.left}
                    x2={PAD.left + plotW}
                    y1={y}
                    y2={y}
                    stroke="var(--grid)"
                    strokeWidth={1}
                  />
                  <text
                    x={PAD.left - 8}
                    y={y + 4}
                    textAnchor="end"
                    fontSize={11}
                    fill="var(--text-muted)"
                    style={{ fontVariantNumeric: 'tabular-nums' }}
                  >
                    {tick}
                  </text>
                </g>
              );
            })}

            {/* Pass threshold, drawn as a solid rule in the axis tone. */}
            <line
              x1={PAD.left}
              x2={PAD.left + plotW}
              y1={PAD.top + plotH - 0.7 * plotH}
              y2={PAD.top + plotH - 0.7 * plotH}
              stroke="var(--axis)"
              strokeWidth={1}
            />

            <line
              x1={PAD.left}
              x2={PAD.left + plotW}
              y1={PAD.top + plotH}
              y2={PAD.top + plotH}
              stroke="var(--axis)"
              strokeWidth={1}
            />

            {areaPath && <path d={areaPath} fill="var(--accent)" opacity={0.1} />}

            <path
              d={linePath}
              fill="none"
              stroke="var(--accent)"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {hovered && (
              <line
                x1={hovered.x}
                x2={hovered.x}
                y1={PAD.top}
                y2={PAD.top + plotH}
                stroke="var(--axis)"
                strokeWidth={1}
              />
            )}

            {/* Markers carry a 2px surface ring so they stay legible on the line. */}
            {coords.map((c, i) => (
              <circle
                key={c.point.attempt_id}
                cx={c.x}
                cy={c.y}
                r={active === i ? 5.5 : 4}
                fill="var(--accent)"
                stroke="var(--surface-1)"
                strokeWidth={2}
              />
            ))}

            {/* Only the endpoint is direct-labelled; the tooltip carries the rest. */}
            <text
              x={last.x + 10}
              y={last.y + 4}
              fontSize={12}
              fontWeight={600}
              fill="var(--text-primary)"
              style={{ fontVariantNumeric: 'tabular-nums' }}
            >
              {last.point.score.toFixed(0)}%
            </text>
          </svg>

          {hovered && (
            <div
              className="pointer-events-none absolute z-10 w-56 -translate-x-1/2 rounded-lg border border-line bg-surface px-3 py-2 text-xs shadow-lg"
              style={{
                left: `${(hovered.x / W) * 100}%`,
                top: `${(hovered.y / H) * 100}%`,
                transform: 'translate(-50%, -115%)',
              }}
            >
              <p className="truncate font-semibold text-ink">{hovered.point.quiz_title}</p>
              <p className="mt-1 text-ink-secondary">
                {t.quizzes.colScore}{' '}
                <span className="tabular-nums">{hovered.point.score}%</span>
              </p>
              <p className="text-ink-muted">
                {formatDateLocale(hovered.point.completed_at, locale)}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ScoreTable({ points }: { points: QuizScorePoint[] }) {
  const { t, locale } = useI18n();
  return (
    <div className="max-h-72 overflow-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-surface">
          <tr className="border-b border-axis text-left text-xs uppercase tracking-wide text-ink-muted">
            <th className="py-2 pr-3 font-medium">{t.quizzes.colQuiz}</th>
            <th className="py-2 pr-3 font-medium">{t.quizzes.colDate}</th>
            <th className="py-2 text-right font-medium">{t.quizzes.colScore}</th>
          </tr>
        </thead>
        <tbody>
          {[...points].reverse().map((point) => (
            <tr key={point.attempt_id} className="border-b border-line">
              <td className="py-2 pr-3 text-ink">{point.quiz_title}</td>
              <td className="py-2 pr-3 text-ink-secondary">
                {formatDateLocale(point.completed_at, locale)}
              </td>
              <td className="py-2 text-right tabular-nums text-ink-secondary">{point.score}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
