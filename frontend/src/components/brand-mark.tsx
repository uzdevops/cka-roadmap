/**
 * The product mark.
 *
 * A lemniscate - the infinity loop the DevOps field has used for itself since
 * the eight-phase wheel - but woven rather than merely crossed: the upper-left
 * and lower-right arms run through the centre as one unbroken stroke while the
 * other two stop short of it, so the loop passes visibly over and under itself.
 *
 * That break is the whole design decision. A plain lemniscate puts two strokes
 * through the same point, and at the 28px the rail renders this at, the two
 * merge into a dark blot exactly where the eye lands first. Cutting the rear
 * strand replaces the blot with negative space, which reads as a hand-off
 * between two loops - dev to ops, build to run - instead of an accident of
 * geometry. Two strokes, one crossing, nothing else: it survives being scaled
 * to a favicon.
 *
 * Drawn on the same 24px grid and with the same round caps as `nav-icons.tsx`,
 * so the rail reads as one drawing. `currentColor` throughout, which is what
 * lets it sit on the gradient tile in either theme - the tile supplies
 * `--gradient-accent` as its background and `--accent-ink` as its colour, the
 * same pairing the mark has always used.
 *
 * It carries no letterform: the product name sits beside it as real text, so
 * this is `aria-hidden` and assistive tech never announces it twice.
 */
export function BrandMark({
  size = 28,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      aria-hidden
      focusable="false"
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.9}
      strokeLinecap="round"
    >
      {/* Left loop: enters the crossing from the upper left and runs straight
          through it. Its lower-left arm stops 3.3 units short - that is the
          gap the right loop passes behind. */}
      <path d="M9.44 14.16C6.94 15.86 4.8 15.9 4.8 12C4.8 6.8 8.61 8.61 12 12" />
      {/* Right loop: the same curve rotated a half turn, so the two tails meet
          at dead centre on a shared tangent and read as one continuous stroke. */}
      <path d="M14.56 9.84C17.06 8.14 19.2 8.1 19.2 12C19.2 17.2 15.39 15.39 12 12" />
    </svg>
  );
}
