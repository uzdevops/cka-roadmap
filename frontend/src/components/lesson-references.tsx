import { NavIcon } from '@/components/nav-icons';
import { Card, CardContent } from '@/components/ui/card';

/**
 * Official documentation for the topic, at the foot of the lesson.
 *
 * Server-rendered from the lesson's structured `references`, so the links
 * survive an admin rewriting the body and a placeholder lesson still carries
 * them. External by definition, so each opens in a new tab.
 */
export function LessonReferences({
  heading,
  newTab,
  references,
}: {
  heading: string;
  newTab: string;
  references: { title: string; url: string }[];
}) {
  if (references.length === 0) return null;

  return (
    <Card>
      <CardContent className="pt-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-muted">
          {heading}
        </h2>
        <ul className="mt-3 flex flex-col gap-2">
          {references.map((ref) => (
            <li key={ref.url}>
              <a
                href={ref.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-start gap-2 text-sm text-ink-secondary hover:text-[var(--accent)]"
              >
                <NavIcon name="resources" size={15} className="mt-0.5 shrink-0" />
                <span>
                  {ref.title}
                  <span aria-hidden className="ml-1 text-[var(--accent)]">
                    ↗
                  </span>
                  <span className="sr-only"> ({newTab})</span>
                  <span className="block text-xs text-ink-muted">
                    {new URL(ref.url).hostname.replace(/^www\./, '')}
                  </span>
                </span>
              </a>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
