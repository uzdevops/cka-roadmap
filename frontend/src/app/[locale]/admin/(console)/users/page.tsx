'use client';

import { useCallback, useEffect, useState } from 'react';

import { StatTile } from '@/components/charts/stat-tile';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FieldError, Input, Label } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { apiFetch } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { AdminUser, Role } from '@/lib/types';

/**
 * User management. Since self-registration is closed, this is the only door
 * into the platform - so it is also where the guards against locking yourself
 * out live, mirrored from the API which enforces them for real.
 */
export default function AdminUsersPage() {
  const { t, fill } = useI18n();
  const { user: me } = useAuth();

  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<Role>('student');
  const [formError, setFormError] = useState<string | null>(null);
  const [created, setCreated] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setUsers(await apiFetch<AdminUser[]>('/admin/users'));
    } catch (err) {
      setError(err instanceof Error ? err.message : t.admin.loadFailed);
    }
  }, [t.admin.loadFailed]);

  useEffect(() => {
    void load();
  }, [load]);

  const create = async (event: React.FormEvent) => {
    event.preventDefault();
    setFormError(null);
    setCreated(null);

    if (password.length < 8) {
      setFormError(t.auth.passwordTooShort);
      return;
    }

    setBusy(true);
    try {
      await apiFetch<AdminUser>('/admin/users', {
        method: 'POST',
        body: { email, username, password, full_name: fullName || null, role },
      });
      setCreated(username);
      setEmail('');
      setUsername('');
      setPassword('');
      setFullName('');
      setRole('student');
      await load();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : t.admin.userCreateFailed);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (target: AdminUser) => {
    if (!window.confirm(fill(t.admin.userDeleteConfirm, { email: target.email }))) return;
    setError(null);
    try {
      await apiFetch(`/admin/users/${target.id}`, { method: 'DELETE' });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.admin.deleteFailed);
    }
  };

  const resetPassword = async (target: AdminUser) => {
    const next = window.prompt(fill(t.admin.userResetPrompt, { email: target.email }));
    if (!next) return;
    setError(null);
    try {
      await apiFetch(`/admin/users/${target.id}`, {
        method: 'PATCH',
        body: { password: next },
      });
      setError(null);
      window.alert(t.admin.userResetDone);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.profile.saveFailed);
    }
  };

  const toggleActive = async (target: AdminUser) => {
    setError(null);
    try {
      await apiFetch(`/admin/users/${target.id}`, {
        method: 'PATCH',
        body: { is_active: !target.is_active },
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.profile.saveFailed);
    }
  };

  if (error && users === null) {
    return <p className="text-sm text-[var(--critical)]">{error}</p>;
  }
  if (users === null) {
    return <p className="text-sm text-ink-muted">{t.common.loading}</p>;
  }

  const students = users.filter((u) => u.role === 'student');
  const active = users.filter((u) => u.is_active);

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <StatTile
          label={t.admin.stats.users}
          value={users.length}
          hint={fill(t.admin.stats.usersHint, {
            students: students.length,
            admins: users.length - students.length,
          })}
        />
        <StatTile
          label={t.admin.userActive}
          value={`${active.length} / ${users.length}`}
          hint={t.admin.userActiveHint}
        />
        <StatTile
          label={t.admin.userAvgProgress}
          value={
            students.length
              ? `${(
                  students.reduce((sum, u) => sum + u.progress_percent, 0) / students.length
                ).toFixed(1)}%`
              : '—'
          }
          hint={t.admin.userAvgProgressHint}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t.admin.userNew}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={create} className="grid gap-4 sm:grid-cols-2">
            <div>
              {/* First, because it is the login name - the email is contact
                  information and cannot be signed in with. */}
              <Label htmlFor="new-username">{t.auth.identifier}</Label>
              <Input
                id="new-username"
                required
                maxLength={64}
                className="font-mono"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="off"
              />
            </div>
            <div>
              <Label htmlFor="new-email">{t.auth.email}</Label>
              <Input
                id="new-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="off"
              />
            </div>
            <div>
              <Label htmlFor="new-name">{t.auth.name}</Label>
              <Input
                id="new-name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                autoComplete="off"
              />
            </div>
            <div>
              <Label htmlFor="new-password">{t.auth.password}</Label>
              <Input
                id="new-password"
                type="text"
                required
                minLength={8}
                placeholder={t.auth.passwordPlaceholder}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="off"
              />
              {/* Shown in the clear on purpose: the admin has to be able to read
                  it back to the person they are creating it for. */}
              <p className="mt-1 text-xs text-ink-muted">{t.admin.userPasswordHint}</p>
            </div>
            <div>
              <Label htmlFor="new-role">{t.admin.userRole}</Label>
              <select
                id="new-role"
                value={role}
                onChange={(e) => setRole(e.target.value as Role)}
                className="h-10 w-full rounded-lg border border-line bg-surface px-3 text-sm text-ink"
              >
                <option value="student">{t.admin.roleStudent}</option>
                <option value="admin">{t.admin.roleAdmin}</option>
              </select>
            </div>

            <div className="sm:col-span-2">
              {formError && <FieldError>{formError}</FieldError>}
              {created && (
                <p className="mb-2 text-sm text-[var(--good-text)]">
                  {fill(t.admin.userCreated, { email: created })}
                </p>
              )}
              <Button type="submit" disabled={busy}>
                {busy ? t.common.saving : t.admin.userCreate}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{fill(t.admin.userCount, { count: users.length })}</CardTitle>
        </CardHeader>
        <CardContent>
          {error && <p className="mb-3 text-sm text-[var(--critical)]">{error}</p>}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-axis text-left text-xs uppercase tracking-wide text-ink-muted">
                  <th className="py-2 pr-3 font-medium">{t.auth.email}</th>
                  <th className="py-2 pr-3 font-medium">{t.admin.userRole}</th>
                  <th className="py-2 pr-3 text-right font-medium">{t.dashboard.colLessons}</th>
                  <th className="py-2 pr-3 text-right font-medium">{t.dashboard.colQuizAvg}</th>
                  <th className="py-2 pr-3 text-right font-medium">{t.admin.userStreak}</th>
                  <th className="py-2 pr-3 font-medium">{t.admin.userLastActive}</th>
                  <th className="py-2 text-right font-medium">{t.admin.colActions}</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => {
                  const self = u.id === me?.id;
                  return (
                    <tr key={u.id} className="border-b border-line">
                      <td className="py-2 pr-3">
                        <span className="text-ink">{u.full_name || u.username || u.email}</span>
                        {/* The login name and the address, both: the first is
                            what they sign in with, the second is who they are. */}
                        <span className="block text-xs text-ink-muted">
                          {u.username && <code className="font-mono">{u.username}</code>}
                          {u.username && ' · '}
                          {u.email}
                        </span>
                      </td>
                      <td className="py-2 pr-3">
                        <Badge variant={u.role === 'admin' ? 'accent' : 'neutral'}>
                          {u.role === 'admin' ? t.admin.roleAdmin : t.admin.roleStudent}
                        </Badge>
                        {!u.is_active && (
                          <Badge variant="warning" className="ml-1">
                            {t.admin.userDisabled}
                          </Badge>
                        )}
                      </td>
                      <td className="py-2 pr-3 text-right tabular-nums text-ink-secondary">
                        {u.completed_lessons}/{u.total_lessons}
                        <span className="block text-xs text-ink-muted">
                          {u.progress_percent}%
                        </span>
                      </td>
                      <td className="py-2 pr-3 text-right tabular-nums text-ink-secondary">
                        {u.quiz_average === null ? '—' : `${u.quiz_average}%`}
                        <span className="block text-xs text-ink-muted">
                          {fill(t.admin.userAttempts, { count: u.quiz_attempts })}
                        </span>
                      </td>
                      <td className="py-2 pr-3 text-right tabular-nums text-ink-secondary">
                        {u.current_streak}
                      </td>
                      <td className="py-2 pr-3 text-ink-secondary">
                        {u.last_active ?? '—'}
                      </td>
                      <td className="py-2 text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => void resetPassword(u)}
                          >
                            {t.admin.userReset}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={self}
                            onClick={() => void toggleActive(u)}
                          >
                            {u.is_active ? t.admin.userDisable : t.admin.userEnable}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={self}
                            onClick={() => void remove(u)}
                          >
                            {t.common.delete}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
