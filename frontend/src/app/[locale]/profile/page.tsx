'use client';

import { useEffect, useState } from 'react';

import { AuthGuard } from '@/components/auth-guard';
import { LanguageSwitcher } from '@/components/language-switcher';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FieldError, Input, Label } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { formatDateLocale } from '@/lib/utils';

export default function ProfilePage() {
  return (
    <AuthGuard>
      <ProfileView />
    </AuthGuard>
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

  return (
    <div className="mx-auto max-w-2xl py-4">
      <h1 className="text-3xl font-semibold tracking-tight text-ink">{t.profile.heading}</h1>
      <p className="mt-2 text-ink-secondary">{t.profile.intro}</p>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>{t.profile.account}</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="flex flex-col gap-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-ink-muted">{t.profile.email}</dt>
              <dd className="text-ink">{user.email}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-ink-muted">{t.profile.role}</dt>
              <dd>
                <Badge variant={user.role === 'admin' ? 'accent' : 'neutral'}>{user.role}</Badge>
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-ink-muted">{t.profile.memberSince}</dt>
              <dd className="text-ink-secondary">{formatDateLocale(user.created_at, locale)}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>{t.profile.languageHeading}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <p className="max-w-md text-sm text-ink-secondary">{t.profile.languageBody}</p>
            <LanguageSwitcher />
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>{t.profile.studyPlan}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={saveProfile}>
            <div className="mb-4">
              <Label htmlFor="name">{t.auth.name}</Label>
              <Input id="name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </div>

            <div className="mb-4">
              <Label htmlFor="exam-date">{t.profile.targetDate}</Label>
              <Input
                id="exam-date"
                type="date"
                value={examDate}
                onChange={(e) => setExamDate(e.target.value)}
              />
            </div>

            <div className="mb-2">
              <Label htmlFor="minutes">{t.profile.dailyMinutes}</Label>
              <Input
                id="minutes"
                type="number"
                min={5}
                max={1440}
                value={minutes}
                onChange={(e) => setMinutes(Number(e.target.value))}
              />
            </div>

            <FieldError>{error}</FieldError>
            {saved && (
              <p className="mt-2 text-sm text-[var(--good-text)]">{t.common.saved}</p>
            )}

            <Button type="submit" className="mt-4" disabled={busy}>
              {busy ? t.common.saving : t.profile.saveChanges}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>{t.profile.changePassword}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={changePassword}>
            <div className="mb-4">
              <Label htmlFor="current">{t.profile.currentPassword}</Label>
              <Input
                id="current"
                type="password"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </div>
            <div className="mb-2">
              <Label htmlFor="new">{t.profile.newPassword}</Label>
              <Input
                id="new"
                type="password"
                autoComplete="new-password"
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>

            <FieldError>{passwordError}</FieldError>
            {passwordMessage && (
              <p className="mt-2 text-sm text-[var(--good-text)]">{passwordMessage}</p>
            )}

            <Button type="submit" variant="secondary" className="mt-4">
              {t.profile.updatePassword}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
