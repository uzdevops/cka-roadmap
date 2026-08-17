import { NextResponse } from 'next/server';

import { renderMarkdown } from '@/lib/markdown';

export const dynamic = 'force-dynamic';

/**
 * Renders markdown with the same pipeline the lesson pages use, so the admin
 * editor's preview matches what students will see exactly.
 */
export async function POST(request: Request) {
  const { markdown } = (await request.json()) as { markdown?: string };
  const html = await renderMarkdown(markdown ?? '');
  return NextResponse.json({ html });
}
