'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Fragment, type ReactNode } from 'react';

import { BrandMark } from '@/components/brand-mark';
import { LanguageSwitcher } from '@/components/language-switcher';
import { NavIcon, type IconName } from '@/components/nav-icons';
import { ThemeToggle } from '@/components/theme-toggle';
import { stripLocale } from '@/i18n/config';
import { useI18n } from '@/i18n/provider';
import { useAuth } from '@/lib/auth-context';
import { cn } from '@/lib/utils';

/**
 * The admin console frame - a different room in the same building.
 *
 * The student site is a wide navigation rail over an atmospheric ground: a
 * place you browse. Management is not browsing, so this surface inverts that
 * arrangement. One dense header carries everything - identity, session, the
 * four editors, the way out - the ground goes flat and tinted with no aurora
 * behind it, and every label in the chrome is set in the mono face. The brand
 * mark, the icon set, the accent hairline and the tokens are unchanged, which
 * is what keeps it the same product.
 *
 * The header also replaces the app rail here (see the `.adm-` block in
 * globals.css): the rail's entries - Panel, Roadmap, Lessons, Labs, References -
 * are read-only mirrors of the student site and are exactly what made the two
 * surfaces indistinguishable. `Student site` below is the deliberate way back.
 *
 * The lockup links to /admin. That route holds the stats overview and is the
 * target of the rail's `Admin` entry, the only link into this surface, so it
 * keeps a home here rather than being orphaned by the loss of its tab.
 */

interface Section {
  path: string;
  label: string;
  icon: IconName;
  group: 'people' | 'content';
}

export function AdminConsole({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { t, href } = useI18n();
  const { user, logout } = useAuth();

  const current = stripLocale(pathname);
  const isAdmin = user?.role === 'admin';

  // Management only: the people, then the three content editors. Nothing here
  // duplicates a page the student site already renders.
  const sections: Section[] = [
    { path: '/admin/users', label: t.admin.tabs.users, icon: 'profile', group: 'people' },
    { path: '/admin/lessons', label: t.admin.tabs.lessons, icon: 'lessons', group: 'content' },
    { path: '/admin/quizzes', label: t.admin.tabs.quizzes, icon: 'quizzes', group: 'content' },
    { path: '/admin/labs', label: t.admin.tabs.labs, icon: 'labs', group: 'content' },
  ];

  const groupLabels: Record<Section['group'], string> = {
    people: t.admin.groupPeople,
    content: t.admin.groupContent,
  };

  // An editor at /admin/lessons/12 still belongs to the Lessons section.
  const isActive = (path: string) => current === path || current.startsWith(`${path}/`);
  const atHome = current === '/admin';
  const heading = sections.find((section) => isActive(section.path))?.label ?? t.admin.tabs.overview;

  return (
    <div className="adm-console">
      <header className="adm-topbar">
        <div className="adm-bar">
          <Link
            href={href('/admin')}
            title={t.admin.consoleHome}
            aria-current={atHome ? 'page' : undefined}
            className="adm-lockup"
          >
            <span aria-hidden className="adm-mark brand-tile">
              <BrandMark size={22} />
            </span>
            <span className="adm-lockup-text">
              <span className="adm-lockup-product">{t.meta.siteName}</span>
              <span className="adm-lockup-title">{t.admin.consoleTitle}</span>
            </span>
          </Link>

          {/* The identity is spelled out, not implied by the tint. */}
          <span className="adm-tag">
            <NavIcon name="admin" size={12} />
            {t.admin.consoleTag}
          </span>

          <div className="adm-tools">
            {user && (
              <Link
                href={href('/profile')}
                className="adm-session"
                // Below 900px the label and the address collapse to this
                // initial, so the control still has a name for a screen reader
                // and still has a target for a thumb.
                aria-label={`${t.admin.session}: ${user.full_name ?? user.email}`}
              >
                <span aria-hidden className="adm-session-initial">
                  {(user.full_name ?? user.email).trim().charAt(0).toUpperCase()}
                </span>
                <span className="adm-session-label">{t.admin.session}</span>
                <span className="adm-session-value">{user.full_name ?? user.email}</span>
              </Link>
            )}

            <Link
              href={href('/dashboard')}
              title={t.admin.backToSiteFull}
              aria-label={t.admin.backToSiteFull}
              className="adm-action adm-exit"
            >
              <span aria-hidden className="adm-exit-arrow">
                ←
              </span>
              <span className="adm-action-text">{t.admin.backToSite}</span>
            </Link>

            <LanguageSwitcher />
            <ThemeToggle />

            <button
              type="button"
              onClick={logout}
              title={t.nav.signOut}
              aria-label={t.nav.signOut}
              className="adm-action"
            >
              <NavIcon name="signout" size={14} />
              <span className="adm-action-text">{t.nav.signOut}</span>
            </button>
          </div>
        </div>

        {isAdmin && (
          <nav className="adm-nav" aria-label={t.admin.consoleNav}>
            {sections.map((section, index) => {
              const active = isActive(section.path);
              const opensGroup = index === 0 || sections[index - 1].group !== section.group;

              return (
                <Fragment key={section.path}>
                  {opensGroup && <span className="adm-group">{groupLabels[section.group]}</span>}
                  <Link
                    href={href(section.path)}
                    aria-current={active ? 'page' : undefined}
                    className={cn('adm-tab', active && 'adm-tab-active')}
                  >
                    <NavIcon name={section.icon} size={15} />
                    <span>{section.label}</span>
                  </Link>
                </Fragment>
              );
            })}
          </nav>
        )}
      </header>

      <div className="adm-body">
        <div className="adm-head">
          <div className="adm-head-row">
            <h1 className="adm-h1">{heading}</h1>
            {/* Where you are, in text. Cheap to read, and it matches the URL. */}
            <span className="adm-path">
              <span className="adm-path-label">{t.admin.pathLabel}</span>
              <code>{current}</code>
            </span>
          </div>
          <p className="adm-note">
            <NavIcon name="admin" size={14} className="adm-note-icon" />
            <span>{t.admin.intro}</span>
          </p>
        </div>

        {children}
      </div>
    </div>
  );
}
