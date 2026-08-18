'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

import { useI18n } from '@/i18n/provider';
import type { PhaseDetail } from '@/lib/types';

/**
 * The roadmap as one continuous path: six phase nodes threaded onto a
 * serpentine line that fills as you progress, ending at the exam.
 *
 * The geometry is fixed in viewBox units and the SVG scales, so the layout is
 * identical at every width and nothing has to be measured to lay it out. Only
 * the week dots need the real element - they are placed with
 * `getPointAtLength`, which is exact and saves re-deriving the arc maths.
 *
 * Below 768px this is replaced by a vertical variant: a serpentine that has to
 * scroll sideways is worse than a list.
 */

const VIEW_W = 1200;
const X0 = 80;
const X1 = VIEW_W - X0;
const Y0 = 96;
const PITCH = 165;
const R = 60;
const ROWS = 3;
const PER_ROW = 2;
const VIEW_H = Y0 + (ROWS - 1) * PITCH + 96;

const rowY = (row: number) => Y0 + row * PITCH;
/** Rows alternate direction; that is what makes it a serpentine. */
const rowGoesRight = (row: number) => row % 2 === 0;

/** The path every layer shares. Built once, from the constants above. */
function buildPath(): string {
  const parts: string[] = [`M ${X0} ${rowY(0)}`];

  for (let row = 0; row < ROWS; row++) {
    const right = rowGoesRight(row);
    const endX = right ? X1 : X0;
    const y = rowY(row);
    const last = row === ROWS - 1;

    if (last) {
      parts.push(`L ${endX} ${y}`);
      break;
    }

    // Run to the turn, quarter-arc down, short vertical, quarter-arc back in.
    const turnIn = right ? endX - R : endX + R;
    const sweep = right ? 1 : 0;
    parts.push(`L ${turnIn} ${y}`);
    parts.push(`A ${R} ${R} 0 0 ${sweep} ${endX} ${y + R}`);
    parts.push(`L ${endX} ${y + PITCH - R}`);
    parts.push(`A ${R} ${R} 0 0 ${sweep} ${turnIn} ${y + PITCH}`);
  }

  return parts.join(' ');
}

const PATH = buildPath();

interface Node {
  phase: PhaseDetail;
  /** 1-based position on the path, independent of how the data numbers phases. */
  index: number;
  x: number;
  y: number;
  row: number;
  /** Labels flip side per row so they never sit on the path. */
  labelAbove: boolean;
  state: 'done' | 'current' | 'locked';
}

function layout(phases: PhaseDetail[]): Node[] {
  const ordered = [...phases].sort((a, b) => a.order_index - b.order_index).slice(0, ROWS * PER_ROW);
  // The first phase that is not finished is where the reader stands.
  const currentIdx = ordered.findIndex((p) => p.progress_percent < 100);

  return ordered.map((phase, i) => {
    const row = Math.floor(i / PER_ROW);
    const slot = i % PER_ROW;
    const right = rowGoesRight(row);
    // Evenly spaced along the row, following its direction.
    const fraction = (slot + 0.5) / PER_ROW;
    const x = right ? X0 + (X1 - X0) * fraction : X1 - (X1 - X0) * fraction;

    return {
      phase,
      index: i + 1,
      x,
      y: rowY(row),
      row,
      labelAbove: true,
      state:
        phase.progress_percent >= 100 ? 'done' : i === currentIdx ? 'current' : 'locked',
    };
  });
}

function eyebrow(phase: PhaseDetail, index: number): string {
  const num = String(index).padStart(2, '0');
  const weeks = `W${phase.week_start}–${phase.week_end}`;
  return phase.exam_weight > 0
    ? `PHASE ${num} · ${weeks} · ${phase.exam_weight}%`
    : `PHASE ${num} · ${weeks}`;
}

export function Serpentine({
  phases,
  overallPercent,
}: {
  phases: PhaseDetail[];
  overallPercent: number;
}) {
  const { t, href, fill } = useI18n();
  const pathRef = useRef<SVGPathElement>(null);
  const [dots, setDots] = useState<{ x: number; y: number; done: boolean }[]>([]);
  const [drawn, setDrawn] = useState(false);
  const [hover, setHover] = useState<Node | null>(null);

  const nodes = layout(phases);
  const totalWeeks = phases.reduce((n, p) => n + (p.week_end - p.week_start + 1), 0);
  const doneWeeks = phases.reduce(
    (n, p) => n + (p.progress_percent >= 100 ? p.week_end - p.week_start + 1 : 0),
    0,
  );

  // Week dots, spaced along the real path rather than re-derived from the arcs.
  useEffect(() => {
    const path = pathRef.current;
    if (!path || totalWeeks === 0) return;
    const len = path.getTotalLength();
    const next = Array.from({ length: totalWeeks }, (_, i) => {
      const at = ((i + 0.5) / totalWeeks) * len;
      const p = path.getPointAtLength(at);
      return { x: p.x, y: p.y, done: i < doneWeeks };
    });
    setDots(next);
  }, [totalWeeks, doneWeeks]);

  // Draw the progress stroke once, after mount.
  useEffect(() => {
    const id = requestAnimationFrame(() => setDrawn(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const progress = Math.max(0, Math.min(100, overallPercent));

  return (
    <div className="relative">
      <svg
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        className="hidden w-full md:block"
        role="group"
        aria-label={t.roadmap.pathLabel}
      >
        <defs>
          <linearGradient id="gradRoadmap" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--accent-2)" />
            <stop offset="55%" stopColor="var(--accent)" />
            <stop offset="100%" stopColor="var(--accent-3)" />
          </linearGradient>
        </defs>

        {/* 1. the track */}
        <path
          ref={pathRef}
          d={PATH}
          fill="none"
          stroke="var(--axis)"
          strokeWidth={3}
          strokeLinecap="round"
        />

        {/* 2. how far you have come */}
        <path
          className="roadmap-progress"
          d={PATH}
          fill="none"
          stroke="url(#gradRoadmap)"
          strokeWidth={3.5}
          strokeLinecap="round"
          pathLength={100}
          strokeDasharray={`${drawn ? progress : 0} 100`}
        />

        {/* 3. one dot per week */}
        {dots.map((d, i) => (
          <circle
            key={i}
            aria-hidden
            cx={d.x}
            cy={d.y}
            r={3.5}
            fill={d.done ? 'var(--accent-2)' : 'var(--axis)'}
          />
        ))}

        {/* 4. the phases */}
        {nodes.map((node) => (
          <PhaseNode
            key={node.phase.slug}
            node={node}
            href={href(`/roadmap/${node.phase.slug}`)}
            hereLabel={t.roadmap.youAreHere}
            ariaLabel={fill(t.roadmap.nodeLabel, {
              phase: node.phase.title,
              done: node.phase.completed_lessons,
              total: node.phase.total_lessons,
            })}
            onEnter={() => setHover(node)}
            onLeave={() => setHover(null)}
          />
        ))}

        {/* 5. the exam, at the end of the line */}
        <g aria-hidden transform={`translate(${X1 - 55} ${rowY(ROWS - 1) - 18})`}>
          <rect
            width={110}
            height={36}
            rx={18}
            fill="color-mix(in srgb, var(--good) 12%, transparent)"
            stroke="var(--good)"
            strokeWidth={1.5}
          />
          <text
            x={55}
            y={23}
            textAnchor="middle"
            className="roadmap-exam-text"
            fill="var(--good-text)"
          >
            {t.roadmap.examCapsule}
          </text>
        </g>
      </svg>

      {hover && <NodeTooltip node={hover} />}

      {/* Vertical variant: same data, no sideways scrolling. */}
      <ol className="flex flex-col gap-3 md:hidden">
        {nodes.map((node) => (
          <li key={node.phase.slug}>
            <Link
              href={href(`/roadmap/${node.phase.slug}`)}
              className="roadmap-vrow card-hover"
              data-state={node.state}
            >
              <span aria-hidden className="roadmap-vdot" />
              <span className="min-w-0">
                <span className="tech-label block">{eyebrow(node.phase, node.index)}</span>
                <span className="mt-0.5 block truncate text-sm font-semibold text-ink">
                  {node.phase.title}
                </span>
                <span className="mt-1 block font-mono text-[11px] text-ink-muted">
                  {node.phase.completed_lessons}/{node.phase.total_lessons}
                </span>
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  );
}

function PhaseNode({
  node,
  href,
  hereLabel,
  ariaLabel,
  onEnter,
  onLeave,
}: {
  node: Node;
  href: string;
  hereLabel: string;
  ariaLabel: string;
  onEnter: () => void;
  onLeave: () => void;
}) {
  const { x, y, state, labelAbove, phase, index } = node;
  const labelY = labelAbove ? y - 40 : y + 44;
  const eyebrowY = labelAbove ? y - 56 : y + 62;

  return (
    <Link href={href} aria-label={ariaLabel}>
      <g
        className="roadmap-node"
        data-state={state}
        onMouseEnter={onEnter}
        onMouseLeave={onLeave}
        onFocus={onEnter}
        onBlur={onLeave}
      >
        {state === 'current' && (
          <circle className="node-pulse" cx={x} cy={y} r={23} fill="var(--accent)" opacity={0.25} />
        )}

        <circle
          cx={x}
          cy={y}
          r={16}
          fill={
            state === 'locked'
              ? 'var(--surface-1)'
              : 'color-mix(in srgb, var(--accent-2) 16%, var(--surface-1))'
          }
          stroke={state === 'locked' ? 'var(--axis)' : 'var(--accent-2)'}
          strokeWidth={2.5}
        />

        <text
          x={x}
          y={y + 5}
          textAnchor="middle"
          className="roadmap-node-glyph"
          fill={state === 'locked' ? 'var(--text-secondary)' : 'var(--accent-2)'}
        >
          {state === 'done' ? '✓' : String(index).padStart(2, '0')}
        </text>

        <text x={x} y={eyebrowY} textAnchor="middle" className="roadmap-eyebrow">
          {eyebrow(phase, node.index)}
        </text>
        <text x={x} y={labelY} textAnchor="middle" className="roadmap-name">
          {phase.title}
        </text>

        {state === 'current' && (
          <g transform={`translate(${x - 48} ${labelAbove ? y + 26 : y - 44})`}>
            <rect width={96} height={18} rx={9} fill="var(--accent)" />
            <text x={48} y={12.5} textAnchor="middle" className="roadmap-here" fill="var(--accent-ink)">
              {hereLabel}
            </text>
          </g>
        )}
      </g>
    </Link>
  );
}

function NodeTooltip({ node }: { node: Node }) {
  const { phase } = node;
  const pct = Math.round(phase.progress_percent);
  return (
    <div
      className="roadmap-tip"
      style={{
        left: `${(node.x / VIEW_W) * 100}%`,
        top: `${((node.y + (node.labelAbove ? 70 : -110)) / VIEW_H) * 100}%`,
      }}
    >
      <p className="text-sm font-semibold text-ink">{phase.title}</p>
      <p className="mt-1 font-mono text-[11px] text-ink-muted">
        {phase.completed_lessons}/{phase.total_lessons} &middot; {pct}%
      </p>
      <span className="roadmap-tip-track">
        <span className="meter-fill block h-full rounded-full" style={{ width: `${pct}%` }} />
      </span>
    </div>
  );
}
