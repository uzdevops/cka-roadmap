'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

import { LanguageSwitcher } from '@/components/language-switcher';
import { ThemeToggle } from '@/components/theme-toggle';
import { Button, ButtonLink } from '@/components/ui/button';
import { stripLocale } from '@/i18n/config';
import { useI18n } from '@/i18n/provider';
import { useAuth } from '@/lib/auth-context';
import { cn } from '@/lib/utils';

export function SiteHeader() {
  const pathname = usePathname();
  const { user, logout, loading } = useAuth();
  const { t, href } = useI18n();
  const [open, setOpen] = useState(false);

  useEffect(() => setOpen(false), [pathname]);

  const current = stripLocale(pathname);
  const nav = [
    { path: '/roadmap', label: t.nav.roadmap },
    { path: '/lessons', label: t.nav.lessons },
    { path: '/quizzes', label: t.nav.quizzes },
    { path: '/labs', label: t.nav.labs },
    { path: '/resources', label: t.nav.resources },
    ...(user ? [{ path: '/dashboard', label: t.nav.dashboard }] : []),
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-[var(--plane)]/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4">
        <Link href={href('/')} className="flex items-center gap-2 font-semibold tracking-tight">
          <span
            aria-hidden
            className="flex h-6 w-6 items-center justify-center rounded-md text-[11px] font-bold text-[var(--accent-ink)]"
            style={{ background: 'var(--accent)' }}
          >
            K8
          </span>
          <span className="text-ink">{t.meta.siteName}</span>
        </Link>

        <nav className="ml-4 hidden items-center gap-1 md:flex">
          {nav.map((item) => (
            <Link
              key={item.path}
              href={href(item.path)}
              className={cn(
                'rounded-lg px-3 py-1.5 text-sm transition-colors',
                current.startsWith(item.path)
                  ? 'bg-[var(--surface-2)] text-ink'
                  : 'text-ink-secondary hover:text-ink',
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <LanguageSwitcher />
          <ThemeToggle />

          {!loading && user ? (
            <div className="hidden items-center gap-2 md:flex">
              {user.role === 'admin' && (
                <ButtonLink href={href('/admin')} variant="ghost" size="sm">
                  {t.nav.admin}
                </ButtonLink>
              )}
              <ButtonLink href={href('/profile')} variant="ghost" size="sm">
                {user.full_name ?? user.email}
              </ButtonLink>
              <Button variant="outline" size="sm" onClick={logout}>
                {t.nav.signOut}
              </Button>
            </div>
          ) : (
            !loading && (
              <div className="hidden items-center gap-2 md:flex">
                <ButtonLink href={href('/login')} variant="ghost" size="sm">
                  {t.nav.signIn}
                </ButtonLink>
                <ButtonLink href={href('/register')} size="sm">
                  {t.nav.getStarted}
                </ButtonLink>
              </div>
            )
          )}

          <button
            type="button"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-line text-ink-secondary md:hidden"
            onClick={() => setOpen((v) => !v)}
            aria-label={t.nav.toggleNav}
            aria-expanded={open}
          >
            <span aria-hidden>{open ? '✕' : '☰'}</span>
          </button>
        </div>
      </div>

      {open && (
        <div className="border-t border-line bg-surface px-4 py-3 md:hidden">
          <nav className="flex flex-col gap-1">
            {nav.map((item) => (
              <Link
                key={item.path}
                href={href(item.path)}
                className="rounded-lg px-3 py-2 text-sm text-ink-secondary hover:bg-[var(--surface-2)] hover:text-ink"
              >
                {item.label}
              </Link>
            ))}
            <div className="mt-2 border-t border-line pt-2">
              {user ? (
                <>
                  {user.role === 'admin' && (
                    <Link
                      href={href('/admin')}
                      className="block rounded-lg px-3 py-2 text-sm text-ink-secondary"
                    >
                      {t.nav.admin}
                    </Link>
                  )}
                  <Link
                    href={href('/profile')}
                    className="block rounded-lg px-3 py-2 text-sm text-ink-secondary"
                  >
                    {t.nav.profile}
                  </Link>
                  <button
                    onClick={logout}
                    className="block w-full rounded-lg px-3 py-2 text-left text-sm text-ink-secondary"
                  >
                    {t.nav.signOut}
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href={href('/login')}
                    className="block rounded-lg px-3 py-2 text-sm text-ink-secondary"
                  >
                    {t.nav.signIn}
                  </Link>
                  <Link
                    href={href('/register')}
                    className="block rounded-lg px-3 py-2 text-sm text-ink-secondary"
                  >
                    {t.nav.getStarted}
                  </Link>
                </>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
