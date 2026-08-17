'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { AuthGuard } from '@/components/auth-guard';
import { useI18n } from '@/i18n/provider';
import { stripLocale } from '@/i18n/config';
import { cn } from '@/lib/utils';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { t, href } = useI18n();
  const current = stripLocale(pathname);

  const tabs = [
    { path: '/admin', label: t.admin.tabs.overview },
    { path: '/admin/users', label: t.admin.tabs.users },
    { path: '/admin/lessons', label: t.admin.tabs.lessons },
    { path: '/admin/quizzes', label: t.admin.tabs.quizzes },
    { path: '/admin/labs', label: t.admin.tabs.labs },
  ];

  return (
    <AuthGuard requireAdmin>
      <div className="py-4">
        <header>
          <h1 className="text-3xl font-semibold tracking-tight text-ink">
            {t.admin.heading}
          </h1>
          <p className="mt-2 text-ink-secondary">{t.admin.intro}</p>
        </header>

        <nav className="mt-6 flex gap-1 border-b border-line">
          {tabs.map((tab) => {
            const active =
              tab.path === '/admin' ? current === '/admin' : current.startsWith(tab.path);
            return (
              <Link
                key={tab.path}
                href={href(tab.path)}
                className={cn(
                  '-mb-px border-b-2 px-3 py-2 text-sm transition-colors',
                  active
                    ? 'border-[var(--accent)] text-ink'
                    : 'border-transparent text-ink-secondary hover:text-ink',
                )}
              >
                {tab.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-8">{children}</div>
      </div>
    </AuthGuard>
  );
}
