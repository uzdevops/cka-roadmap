'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FieldError, Input, Label } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { BROWSER_API_URL } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

export default function RegisterPage() {
  const router = useRouter();
  const { register, config } = useAuth();
  const { t, href } = useI18n();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (password.length < 8) {
      setError(t.auth.passwordTooShort);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await register(email, password, fullName);
      router.push(href('/dashboard'));
    } catch (err) {
      setError(err instanceof Error ? err.message : t.auth.registerFailed);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-md py-8">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">{t.auth.registerHeading}</h1>
      <p className="mt-2 text-sm text-ink-secondary">{t.auth.registerSubtitle}</p>

      <Card className="mt-6">
        <CardContent className="pt-5">
          <form onSubmit={submit} noValidate>
            <div className="mb-4">
              <Label htmlFor="name">{t.auth.name}</Label>
              <Input
                id="name"
                autoComplete="name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder={t.auth.namePlaceholder}
              />
            </div>

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
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t.auth.passwordPlaceholder}
              />
            </div>

            <FieldError>{error}</FieldError>

            <Button type="submit" className="mt-4 w-full" disabled={busy}>
              {busy ? t.auth.registering : t.auth.registerButton}
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

          <p className="mt-5 text-center text-sm text-ink-secondary">
            {t.auth.haveAccount}{' '}
            <Link href={href('/login')} className="text-[var(--accent)] hover:underline">
              {t.auth.signInLink}
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
