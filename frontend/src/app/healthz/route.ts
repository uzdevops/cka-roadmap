import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

/** Liveness: is the Node process serving? Deliberately touches nothing else. */
export function GET() {
  return NextResponse.json({ status: 'ok' });
}
