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
import { listTracks } from '@/lib/tracks-api';
import type { AdminUser, Role, Track } from '@/lib/types';

/** How much of the catalogue this account opens. */
type AccessMode = 'full' | 'topics' | 'certs' | 'custom';

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
  const [accessMode, setAccessMode] = useState<AccessMode>('full');
  const [chosenTracks, setChosenTracks] = useState<string[]>([]);
  const [tracks, setTracks] = useState<Track[]>([]);
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
    // An admin sees every track, so this is the whole catalogue - exactly the
    // set of grants that can be handed out.
    listTracks().then(setTracks, () => setTracks([]));
  }, [load]);

  const toggleTrack = (slug: string) =>
    setChosenTracks((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug],
    );

  const create = async (event: React.FormEvent) => {
    event.preventDefault();
    setFormError(null);
    setCreated(null);

    if (password.length < 8) {
      setFormError(t.auth.passwordTooShort);
      return;
    }
    if (role === 'student' && accessMode === 'custom' && chosenTracks.length === 0) {
      setFormError(t.admin.accessCustomEmpty);
      return;
    }

    // The three broad modes are the category pair; only "custom" sends the
    // allowlist, and then the categories are ignored by the server anyway.
    const grants =
      role === 'admin' || accessMode === 'full'
        ? { access_topics: true, access_certificates: true, access_tracks: null }
        : accessMode === 'topics'
          ? { access_topics: true, access_certificates: false, access_tracks: null }
          : accessMode === 'certs'
            ? { access_topics: false, access_certificates: true, access_tracks: null }
            : { access_topics: true, access_certificates: true, access_tracks: chosenTracks };

    setBusy(true);
    try {
      await apiFetch<AdminUser>('/admin/users', {
        method: 'POST',
        body: { email, username, password, full_name: fullName || null, role, ...grants },
      });
      setCreated(username);
      setEmail('');
      setUsername('');
      setPassword('');
      setFullName('');
      setRole('student');
      setAccessMode('full');
      setChosenTracks([]);
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

            {/* An admin sees everything by definition, so the grant picker
                only exists for students. */}
            {role === 'student' && (
              <div>
                <Label htmlFor="new-access">{t.admin.accessLabel}</Label>
                <select
                  id="new-access"
                  value={accessMode}
                  onChange={(e) => setAccessMode(e.target.value as AccessMode)}
                  className="h-10 w-full rounded-lg border border-line bg-surface px-3 text-sm text-ink"
                >
                  <option value="full">{t.admin.accessFull}</option>
                  <option value="topics">{t.admin.accessTopicsOnly}</option>
                  <option value="certs">{t.admin.accessCertsOnly}</option>
                  <option value="custom">{t.admin.accessCustom}</option>
                </select>
              </div>
            )}

            {role === 'student' && accessMode === 'custom' && (
              <fieldset className="sm:col-span-2">
                <legend className="sr-only">{t.admin.accessCustom}</legend>
                <div className="grid gap-4 sm:grid-cols-2">
                  {(
                    [
                      // A dual-nature track (CKA is both) is listed once, with
                      // the certificates - that is where people look for it.
                      [t.admin.accessGroupCerts, tracks.filter((tr) => tr.is_certificate)],
                      [
                        t.admin.accessGroupTopics,
                        tracks.filter((tr) => tr.is_topic && !tr.is_certificate),
                      ],
                    ] as const
                  ).map(([groupLabel, group]) => (
                    <div key={groupLabel}>
                      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-muted">
                        {groupLabel}
                      </p>
                      <div className="flex flex-col gap-1.5">
                        {group.map((tr) => (
                          <label
                            key={tr.slug}
                            className="flex cursor-pointer items-center gap-2 text-sm text-ink"
                          >
                            <input
                              type="checkbox"
                              checked={chosenTracks.includes(tr.slug)}
                              onChange={() => toggleTrack(tr.slug)}
                              className="h-4 w-4 accent-[var(--accent)]"
                            />
                            <span>{tr.title}</span>
                            <code className="text-xs text-ink-muted">{tr.slug}</code>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </fieldset>
            )}

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
                        {u.role !== 'admin' && (
                          <span
                            className="block text-xs text-ink-muted"
                            // The allowlist itself, when there is one - the
                            // label alone would hide WHICH tracks were granted.
                            title={u.access_tracks?.join(', ') ?? undefined}
                          >
                            {u.role_label}
                            {u.access_tracks ? `: ${u.access_tracks.join(', ')}` : ''}
                          </span>
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
