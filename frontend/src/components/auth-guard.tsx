'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect, type ReactNode } from 'react';

import { stripLocale } from '@/i18n/config';
import { useI18n } from '@/i18n/provider';
import { useAuth } from '@/lib/auth-context';

/**
 * Client-side route guard. The backend enforces authorisation on every
 * endpoint; this only spares the user a screen full of failed requests.
 */
export function AuthGuard({
  children,
  requireAdmin = false,
}: {
  children: ReactNode;
  requireAdmin?: boolean;
}) {
  const { user, loading } = useAuth();
  const { t, href, fill } = useI18n();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      const next = encodeURIComponent(stripLocale(pathname));
      router.replace(href(`/login?next=${next}`));
    }
  }, [user, loading, router, pathname, href]);

  if (loading) {
    return <div className="py-24 text-center text-sm text-ink-muted">{t.common.loading}</div>;
  }

  if (!user) return null;

  if (requireAdmin && user.role !== 'admin') {
    return (
      <div className="py-24 text-center">
        <h1 className="text-xl font-semibold text-ink">{t.auth.adminOnly}</h1>
        <p className="mt-2 text-sm text-ink-secondary">
          {fill(t.auth.adminOnlyBody, { email: user.email })}
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
