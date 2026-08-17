'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FieldError, Input, Label } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { BROWSER_API_URL } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { login, config } = useAuth();
  const { t, href } = useI18n();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const next = href(params.get('next') ?? '/dashboard');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      router.push(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.auth.signInFailed);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-md py-8">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">{t.auth.signInHeading}</h1>
      <p className="mt-2 text-sm text-ink-secondary">{t.auth.signInSubtitle}</p>

      <Card className="mt-6">
        <CardContent className="pt-5">
          <form onSubmit={submit} noValidate>
            <div className="mb-4">
              <Label htmlFor="email">{t.auth.email}</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </div>

            <div className="mb-2">
              <Label htmlFor="password">{t.auth.password}</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>

            <FieldError>{error}</FieldError>

            <Button type="submit" className="mt-4 w-full" disabled={busy}>
              {busy ? t.auth.signingIn : t.auth.signInButton}
            </Button>
          </form>

          {config?.google_oauth_enabled && (
            <>
              <div className="my-5 flex items-center gap-3">
                <span className="h-px flex-1 bg-[var(--border)]" />
                <span className="text-xs uppercase tracking-wide text-ink-muted">
                  {t.common.or}
                </span>
                <span className="h-px flex-1 bg-[var(--border)]" />
              </div>
              <a
                href={`${BROWSER_API_URL}/api/v1/auth/google/authorize`}
                className="flex h-10 w-full items-center justify-center gap-2 rounded-lg border border-line text-sm font-medium text-ink transition-colors hover:bg-[var(--surface-2)]"
              >
                {t.auth.google}
              </a>
            </>
          )}

          {/* Self-registration is closed; accounts come from an administrator. */}
          <p className="mt-5 text-center text-sm text-ink-muted">{t.auth.noSignUp}</p>
        </CardContent>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="py-16 text-center text-ink-muted" />}>
      <LoginForm />
    </Suspense>
  );
}
