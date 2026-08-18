'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState, type ReactNode } from 'react';

import { LanguageSwitcher } from '@/components/language-switcher';
import { NavIcon, type IconName } from '@/components/nav-icons';
import { ThemeToggle } from '@/components/theme-toggle';
import { stripLocale } from '@/i18n/config';
import { useI18n } from '@/i18n/provider';
import { useAuth } from '@/lib/auth-context';
import { cn } from '@/lib/utils';

/**
 * The application frame: a fixed navigation rail on the left, a slim top bar,
 * and the page itself.
 *
 * A rail rather than a top nav because this is a tool people keep open, not a
 * site they pass through - the sections stay visible and the horizontal space a
 * top nav would have eaten goes to the content instead.
 *
 * The login screen renders bare: there is nothing to navigate to yet.
 */

interface NavItem {
  path: string;
  label: string;
  icon: IconName;
}

function useNav(): { main: NavItem[]; admin: NavItem[] } {
  const { t } = useI18n();
  const { user } = useAuth();

  return {
    main: [
      { path: '/dashboard', label: t.nav.dashboard, icon: 'dashboard' },
      { path: '/roadmap', label: t.nav.roadmap, icon: 'roadmap' },
      { path: '/lessons', label: t.nav.lessons, icon: 'lessons' },
      { path: '/quizzes', label: t.nav.quizzes, icon: 'quizzes' },
      { path: '/labs', label: t.nav.labs, icon: 'labs' },
      { path: '/resources', label: t.nav.resources, icon: 'resources' },
    ],
    admin:
      user?.role === 'admin'
        ? [{ path: '/admin', label: t.nav.admin, icon: 'admin' }]
        : [],
  };
}

function NavLink({ item, onNavigate }: { item: NavItem; onNavigate?: () => void }) {
  const pathname = usePathname();
  const { href } = useI18n();
  const current = stripLocale(pathname);

  // `/` is the dashboard, so the dashboard entry owns both.
  const active =
    item.path === '/dashboard'
      ? current === '/' || current.startsWith('/dashboard')
      : current.startsWith(item.path);

  return (
    <Link
      href={href(item.path)}
      onClick={onNavigate}
      aria-current={active ? 'page' : undefined}
      className={cn('rail-link', active && 'rail-link-active')}
    >
      <NavIcon name={item.icon} />
      <span>{item.label}</span>
    </Link>
  );
}

function Rail({ onNavigate }: { onNavigate?: () => void }) {
  const { t, href } = useI18n();
  const { user, logout } = useAuth();
  const { main, admin } = useNav();

  return (
    <div className="flex h-full flex-col">
      <Link href={href('/')} onClick={onNavigate} className="rail-brand">
        <span aria-hidden className="rail-mark">
          K8
        </span>
        <span>{t.meta.siteName}</span>
      </Link>

      <nav className="mt-2 flex flex-1 flex-col gap-0.5 px-3">
        {main.map((item) => (
          <NavLink key={item.path} item={item} onNavigate={onNavigate} />
        ))}

        {admin.length > 0 && (
          <>
            <span className="rail-divider" />
            {admin.map((item) => (
              <NavLink key={item.path} item={item} onNavigate={onNavigate} />
            ))}
          </>
        )}
      </nav>

      <div className="border-t border-line p-3">
        <Link href={href('/profile')} onClick={onNavigate} className="rail-user">
          <span aria-hidden className="rail-avatar">
            {(user?.full_name ?? user?.email ?? '?').charAt(0).toUpperCase()}
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm text-ink">
              {user?.full_name ?? user?.email}
            </span>
            <span className="block truncate text-xs text-ink-muted">
              {user?.role === 'admin' ? t.admin.roleAdmin : t.admin.roleStudent}
            </span>
          </span>
        </Link>
        <button type="button" onClick={logout} className="rail-link mt-1 w-full">
          <NavIcon name="signout" />
          <span>{t.nav.signOut}</span>
        </button>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { t } = useI18n();
  const [open, setOpen] = useState(false);

  const bare = stripLocale(pathname);
  const bareLayout = bare === '/login' || bare.startsWith('/auth/');

  useEffect(() => setOpen(false), [pathname]);

  if (bareLayout) {
    return (
      <div className="flex min-h-screen flex-col">
        <div className="flex justify-end gap-2 p-4">
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
        <main className="flex flex-1 items-start justify-center px-4">{children}</main>
      </div>
    );
  }

  return (
    <div className="min-h-screen lg:flex">
      {/* Desktop rail */}
      <aside className="app-rail hidden lg:flex">
        <Rail />
      </aside>

      {/* Mobile drawer */}
      {open && (
        <>
          <button
            type="button"
            aria-label={t.nav.toggleNav}
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            onClick={() => setOpen(false)}
          />
          <aside className="app-rail fixed inset-y-0 left-0 z-50 flex lg:hidden">
            <Rail onNavigate={() => setOpen(false)} />
          </aside>
        </>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="app-topbar">
          <button
            type="button"
            className="app-topbar-menu lg:hidden"
            onClick={() => setOpen(true)}
            aria-label={t.nav.toggleNav}
            aria-expanded={open}
          >
            <NavIcon name="menu" size={20} />
          </button>

          <div className="ml-auto flex items-center gap-2">
            <LanguageSwitcher />
            <ThemeToggle />
          </div>
        </header>

        <main className="app-main">{children}</main>
      </div>
    </div>
  );
}
