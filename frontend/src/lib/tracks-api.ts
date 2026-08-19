/**
 * Track and enrollment calls.
 *
 * Separate from `lib/api.ts` because these are the few endpoints that name a
 * track in their PATH rather than taking the ambient `?track=`: they are about
 * a specific track, not about "the one I am looking at". `apiFetch` still adds
 * the ambient parameter, which the backend ignores when the path carries a slug.
 */

import { apiFetch } from '@/lib/api';
import type { Enrollment, Track } from '@/lib/types';

export function listTracks(signal?: AbortSignal): Promise<Track[]> {
  return apiFetch<Track[]>('/tracks', { signal });
}

export function getEnrollment(slug: string, signal?: AbortSignal): Promise<Enrollment> {
  return apiFetch<Enrollment>(`/tracks/${slug}/enrollment`, { signal });
}

export function startTrack(slug: string): Promise<Enrollment> {
  return apiFetch<Enrollment>(`/tracks/${slug}/start`, { method: 'POST' });
}

export function restartTrack(slug: string): Promise<Enrollment> {
  return apiFetch<Enrollment>(`/tracks/${slug}/restart`, { method: 'POST' });
}

/** `null` restores the date the roadmap suggests. */
export function setTargetDate(slug: string, target: string | null): Promise<Enrollment> {
  return apiFetch<Enrollment>(`/tracks/${slug}/enrollment`, {
    method: 'PATCH',
    body: { target_date: target },
  });
}
