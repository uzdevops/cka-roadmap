'use client';

import { DashboardView } from '@/components/dashboard/dashboard-view';

/**
 * The home page is the dashboard.
 *
 * There is no logged-out view any more: `middleware.ts` sends anyone without a
 * session to /login before this renders, so there is nothing to switch on.
 */
export default function HomePage() {
  return <DashboardView />;
}
