/**
 * Line-art icons for the sidebar.
 *
 * Hand-drawn on a 24px grid at a single stroke weight so the rail reads as one
 * set. `currentColor` throughout, which is what lets the active item light up
 * with the accent without a second copy of each path.
 */

type IconName =
  | 'dashboard'
  | 'tracks'
  | 'roadmap'
  | 'lessons'
  | 'quizzes'
  | 'labs'
  | 'resources'
  | 'admin'
  | 'profile'
  | 'signout'
  | 'menu'
  | 'close';

const PATHS: Record<IconName, string> = {
  // Four panels - the dashboard's own shape.
  dashboard: 'M4 4h6v6H4z M14 4h6v4h-6z M14 12h6v8h-6z M4 14h6v6H4z',
  // Three stacked planes: the programmes of study, one above the other.
  tracks: 'M12 3.5 20.5 8 12 12.5 3.5 8z M3.5 12l8.5 4.5 8.5-4.5 M3.5 16l8.5 4.5 8.5-4.5',
  // A route with stops.
  roadmap: 'M7 4v10 M7 18.5v.5 M17 5v.5 M17 10v10 M7 6.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z M17 22a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z M9.5 4h5a2.5 2.5 0 0 1 2.5 2.5',
  // An open book.
  lessons: 'M12 6.5C10.5 5 8.5 4.5 4 4.5v13c4.5 0 6.5.5 8 2 1.5-1.5 3.5-2 8-2v-13c-4.5 0-6.5.5-8 2z M12 6.5v13',
  // A ticked answer sheet.
  quizzes: 'M5 3.5h14v17H5z M8.5 8.5l1.5 1.5 3-3 M8.5 15l1.5 1.5 3-3',
  // A terminal prompt.
  labs: 'M3 5h18v14H3z M6.5 9.5l2.5 2.5-2.5 2.5 M12.5 14.5h5',
  // A bookmark with an outbound arrow.
  resources: 'M6 3.5h9v17l-4.5-3.5L6 20.5z M18 3.5v6 M18 3.5h-3.5',
  // A shield.
  admin: 'M12 2.5 20 5.5v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10v-6z M9 12l2 2 4-4',
  // A person.
  profile: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M4.5 20.5a7.5 7.5 0 0 1 15 0',
  // A door with an arrow leaving it.
  signout: 'M14 4.5H6v15h8 M11 12h9 M17 8.5l3.5 3.5-3.5 3.5',
  menu: 'M4 7h16 M4 12h16 M4 17h16',
  close: 'M6 6l12 12 M18 6L6 18',
};

export function NavIcon({
  name,
  size = 18,
  className,
}: {
  name: IconName;
  size?: number;
  className?: string;
}) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}

export type { IconName };
