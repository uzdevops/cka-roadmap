'use client';

import { useEffect, useState, type ReactNode } from 'react';

import { DashboardView } from '@/components/dashboard/dashboard-view';
import { useI18n } from '@/i18n/provider';
import { tokenStore } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

/**
 * Decides what `/` shows: the dashboard when someone is signed in, the landing
 * page when they are not.
 *
 * Sessions live in localStorage, so the server cannot know which to render. It
 * always renders the landing - that is the page guests and crawlers need, and
 * it keeps the route indexable. The swap happens after mount:
 *
 * - Before mount we must reproduce the server's markup exactly, or React
 *   reports a hydration mismatch. So: landing.
 * - After mount, a token in storage means a dashboard is almost certainly
 *   coming. Showing the placeholder rather than the landing avoids flashing
 *   marketing copy at a returning user for the length of one `/auth/me` call.
 */
export function HomeSwitch({ landing }: { landing: ReactNode }) {
  const { user, loading } = useAuth();
  const { t } = useI18n();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) return <>{landing}</>;

  if (loading && tokenStore.access) {
    return <p className="py-16 text-center text-sm text-ink-muted">{t.dashboard.loading}</p>;
  }

  return user ? <DashboardView /> : <>{landing}</>;
}
