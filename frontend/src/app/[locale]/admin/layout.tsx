import { AuthGuard } from '@/components/auth-guard';

import { AdminConsole } from './_components/admin-console';

/**
 * Everything under /admin is wrapped in the console chrome, including the
 * "admin only" refusal the guard renders for a signed-in student: without the
 * chrome that page would have no way back to the student site, because the
 * console hides the app rail.
 */
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminConsole>
      <AuthGuard requireAdmin>{children}</AuthGuard>
    </AdminConsole>
  );
}
