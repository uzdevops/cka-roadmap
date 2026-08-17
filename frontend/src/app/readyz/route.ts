import { NextResponse } from 'next/server';

import { serverApiUrl } from '@/lib/api';

export const dynamic = 'force-dynamic';

/**
 * Readiness: can this instance actually render pages? Every server-rendered
 * page needs the API, so an unreachable backend means "not ready".
 */
export async function GET() {
  try {
    const res = await fetch(`${serverApiUrl()}/healthz`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) throw new Error(`api returned ${res.status}`);
  } catch (error) {
    return NextResponse.json(
      { status: 'unavailable', api: error instanceof Error ? error.message : 'unreachable' },
      { status: 503 },
    );
  }
  return NextResponse.json({ status: 'ready', api: 'ok' });
}
