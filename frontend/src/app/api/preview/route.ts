import { NextResponse } from 'next/server';

import { normalizeLocale } from '@/i18n/config';
import { renderMarkdown } from '@/lib/markdown';

export const dynamic = 'force-dynamic';

/**
 * Renders markdown with the same pipeline the lesson pages use, so the admin
 * editor's preview matches what students will see exactly - including the
 * locale, which the architecture diagram's labels depend on.
 */
export async function POST(request: Request) {
  const { markdown, locale } = (await request.json()) as {
    markdown?: string;
    locale?: string;
  };
  const html = await renderMarkdown(markdown ?? '', normalizeLocale(locale));
  return NextResponse.json({ html });
}
