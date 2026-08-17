/**
 * One line-art glyph per roadmap phase, so a week card is identifiable at a
 * glance without reading it. Colour carries phase identity elsewhere in the
 * app; the glyph is the redundant, non-colour half of that pairing.
 *
 * Deliberately simple geometry - these render at 16px inside a week card.
 */

const GLYPHS = [
  // 1. Foundations - the Kubernetes heptagon.
  <path
    key="foundations"
    d="M12 2.6 20 7v10l-8 4.4L4 17V7z M12 7.4v9.2 M8 9.6l8 4.8 M16 9.6l-8 4.8"
  />,
  // 2. Workloads & scheduling - stacked Pods.
  <path key="workloads" d="M3.5 6.5h7v7h-7z M13.5 10.5h7v7h-7z M10.5 10h3" />,
  // 3. Networking & storage - a hub with three spokes.
  <path
    key="networking"
    d="M12 9.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z M12 9.5V4 M9.9 13.3 5.2 18 M14.1 13.3 18.8 18"
  />,
  // 4. Cluster architecture - a control plane over two nodes.
  <path
    key="cluster"
    d="M7.5 3.5h9v5h-9z M3 15.5h6v5H3z M15 15.5h6v5h-6z M12 8.5v3 M6 15.5v-4h12v4"
  />,
  // 5. Troubleshooting - a magnifier over a fault.
  <path key="troubleshooting" d="M10.5 4a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13z M15.4 15.4 20 20 M10.5 7.5v4 M10.5 13.6v.1" />,
  // 6. Mock exams - a checked sheet.
  <path
    key="mock-exams"
    d="M5.5 3h13v18h-13z M8.5 8h7 M8.5 12h7 M8.5 16h4"
  />,
];

export function PhaseGlyph({
  index,
  className,
  size = 16,
}: {
  /** Phase `order_index`; anything outside the roadmap falls back to the logo. */
  index: number;
  className?: string;
  size?: number;
}) {
  const glyph = GLYPHS[index] ?? GLYPHS[0];

  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {glyph}
    </svg>
  );
}
