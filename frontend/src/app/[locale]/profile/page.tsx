'use client';

import { useEffect, useState, type ReactNode } from 'react';

import { AuthGuard } from '@/components/auth-guard';
import { LanguageSwitcher } from '@/components/language-switcher';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FieldError, Input, Label } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { formatDateLocale, formatMinutes } from '@/lib/utils';

export default function ProfilePage() {
  return (
    <AuthGuard>
      <ProfileView />
    </AuthGuard>
  );
}

/**
 * One mono eyebrow per section, then the card. The eyebrow sits outside the
 * card so the stack reads as a labelled list of settings rather than four
 * competing headings.
 */
function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="tech-label">{title}</h2>
      <Card className="mt-2">
        <CardContent className="pt-5">{children}</CardContent>
      </Card>
    </section>
  );
}

function Saved({ children }: { children: ReactNode }) {
  return (
    <p className="mt-3 flex items-center gap-1.5 text-sm text-[var(--good-text)]">
      {/* A glyph as well as the colour, so the state survives a mono screen. */}
      <span aria-hidden>✓</span>
      {children}
    </p>
  );
}

function ProfileView() {
  const { user, refreshUser } = useAuth();
  const { t, locale } = useI18n();

  const [fullName, setFullName] = useState('');
  const [examDate, setExamDate] = useState('');
  const [minutes, setMinutes] = useState(60);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    setFullName(user.full_name ?? '');
    setExamDate(user.target_exam_date ?? '');
    setMinutes(user.daily_study_minutes);
  }, [user]);

  const saveProfile = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      await apiFetch('/auth/me', {
        method: 'PATCH',
        body: {
          full_name: fullName || null,
          target_exam_date: examDate || null,
          daily_study_minutes: minutes,
        },
      });
      await refreshUser();
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.profile.saveFailed);
    } finally {
      setBusy(false);
    }
  };

  const changePassword = async (event: React.FormEvent) => {
    event.preventDefault();
    setPasswordError(null);
    setPasswordMessage(null);
    if (newPassword.length < 8) {
      setPasswordError(t.auth.passwordTooShort);
      return;
    }
    try {
      await apiFetch('/auth/me/password', {
        method: 'POST',
        body: { current_password: currentPassword, new_password: newPassword },
      });
      setPasswordMessage(t.profile.passwordUpdated);
      setCurrentPassword('');
      setNewPassword('');
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : t.profile.passwordFailed);
    }
  };

  if (!user) return null;

  const initial = (user.full_name ?? user.email).charAt(0).toUpperCase();
  const isAdmin = user.role === 'admin';
  // A cleared number field reads back as 0 (and, defensively, NaN); neither
  // should print as a study time.
  const minutesLabel = formatMinutes(
    Number.isFinite(minutes) && minutes > 0 ? minutes : 0,
    t.common.minutes,
  );

  return (
    <div className="mx-auto max-w-3xl py-4">
      <header>
        <h1 className="text-[28px] font-bold tracking-[-0.02em] text-ink">{t.profile.heading}</h1>
        <p className="mt-2 max-w-xl text-ink-secondary">{t.profile.intro}</p>
      </header>

      <section className="mt-8">
        <h2 className="tech-label">{t.profile.account}</h2>

        <div className="panel-glass mt-2 rounded-card p-5">
          <div className="flex items-center gap-4">
            <span aria-hidden className="auth-mark">
              {initial}
            </span>
            <p className="min-w-0 flex-1 truncate text-lg font-semibold tracking-[-0.01em] text-ink">
              {user.full_name ?? user.email}
            </p>
          </div>

          <dl className="mt-5 grid gap-4 border-t border-line pt-5 sm:grid-cols-3">
            <div className="min-w-0">
              <dt className="tech-label">{t.profile.email}</dt>
              <dd className="mt-1.5 truncate font-mono text-sm text-ink">{user.email}</dd>
            </div>
            <div className="min-w-0">
              <dt className="tech-label">{t.profile.role}</dt>
              <dd className="mt-1.5">
                <Badge variant={isAdmin ? 'accent' : 'neutral'}>
                  {isAdmin ? t.admin.roleAdmin : t.admin.roleStudent}
                </Badge>
              </dd>
            </div>
            <div className="min-w-0">
              <dt className="tech-label">{t.profile.memberSince}</dt>
              <dd className="mt-1.5 font-mono text-sm text-ink">
                {formatDateLocale(user.created_at, locale)}
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <Section title={t.profile.languageHeading}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <p className="max-w-md text-sm text-ink-secondary">{t.profile.languageBody}</p>
          <LanguageSwitcher />
        </div>
      </Section>

      <Section title={t.profile.studyPlan}>
        <form onSubmit={saveProfile}>
          <div className="mb-4">
            <Label htmlFor="name">{t.auth.name}</Label>
            <Input
              id="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder={t.auth.namePlaceholder}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="exam-date">{t.profile.targetDate}</Label>
              <Input
                id="exam-date"
                type="date"
                className="font-mono"
                value={examDate}
                onChange={(e) => setExamDate(e.target.value)}
              />
            </div>

            <div>
              <div className="mb-1.5 flex items-baseline justify-between gap-3">
                <Label htmlFor="minutes" className="mb-0">
                  {t.profile.dailyMinutes}
                </Label>
                {/* Live readout of the raw number, in the same unit the rest of
                    the app prints study time in. */}
                <span className="shrink-0 font-mono text-[11px] text-ink-muted">
                  {minutesLabel}
                </span>
              </div>
              <Input
                id="minutes"
                type="number"
                min={5}
                max={1440}
                className="font-mono"
                value={minutes}
                onChange={(e) => setMinutes(Number(e.target.value))}
              />
            </div>
          </div>

          <FieldError>{error}</FieldError>
          {saved && <Saved>{t.common.saved}</Saved>}

          <Button type="submit" className="mt-5" disabled={busy}>
            {busy ? t.common.saving : t.profile.saveChanges}
          </Button>
        </form>
      </Section>

      <Section title={t.profile.changePassword}>
        <form onSubmit={changePassword}>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="current">{t.profile.currentPassword}</Label>
              <Input
                id="current"
                type="password"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="new">{t.profile.newPassword}</Label>
              <Input
                id="new"
                type="password"
                autoComplete="new-password"
                minLength={8}
                placeholder={t.auth.passwordPlaceholder}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
          </div>

          <FieldError>{passwordError}</FieldError>
          {passwordMessage && <Saved>{passwordMessage}</Saved>}

          <Button type="submit" variant="secondary" className="mt-5">
            {t.profile.updatePassword}
          </Button>
        </form>
      </Section>
    </div>
  );
}
