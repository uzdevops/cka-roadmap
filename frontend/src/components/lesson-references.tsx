import { NavIcon } from '@/components/nav-icons';
import { Card, CardContent } from '@/components/ui/card';

/** Bare host, for the mono line under each title. Never throws on bad input. */
function hostOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
}

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
        <h2 className="tech-label">{heading}</h2>
        <div aria-hidden className="lsnd-rule mt-2.5" />

        <ul className="mt-3 flex flex-col gap-1">
          {references.map((ref) => (
            <li key={ref.url}>
              <a
                href={ref.url}
                target="_blank"
                rel="noopener noreferrer"
                className="lsnd-ref flex items-start gap-2.5"
              >
                <NavIcon
                  name="resources"
                  size={15}
                  className="lsnd-ref-icon mt-0.5 shrink-0"
                />
                <span className="min-w-0 flex-1">
                  <span className="lsnd-ref-title block text-sm">
                    {ref.title}
                    <span aria-hidden className="lsnd-ref-arrow">
                      ↗
                    </span>
                    <span className="sr-only"> ({newTab})</span>
                  </span>
                  <span className="mt-0.5 block font-mono text-[10px] tracking-[0.04em] text-ink-muted">
                    {hostOf(ref.url)}
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
