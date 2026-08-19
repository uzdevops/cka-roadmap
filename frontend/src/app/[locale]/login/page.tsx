'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';

import { BrandMark } from '@/components/brand-mark';
import { Button, buttonVariants } from '@/components/ui/button';
import { FieldError, Input, Label } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { BROWSER_API_URL } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { cn } from '@/lib/utils';

/**
 * Sign in - the one screen that renders without the navigation rail, so it is
 * also the one screen that gets the aurora at full strength: `.auth-aurora` is
 * a second, page-local wash layered over the global one, with the form floating
 * on a glass panel above it.
 *
 * Behaviour is unchanged: the `next` query parameter still decides where a
 * successful sign in lands, Google only appears when the server says it is
 * configured, and there is deliberately no sign-up path - accounts come from an
 * administrator.
 */
function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { login, config } = useAuth();
  const { t, href } = useI18n();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const next = href(params.get('next') ?? '/dashboard');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(identifier, password);
      router.push(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : t.auth.signInFailed);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-stage w-full max-w-[26rem]">
      <div aria-hidden className="auth-aurora" />

      <header className="flex flex-col items-center text-center">
        {/* Same tile as the rail, three sizes up. The mark is decorative: the
            product name is the <h1> directly beneath it. */}
        <span aria-hidden className="auth-mark auth-mark-lg brand-tile">
          <BrandMark size={60} />
        </span>
        <h1 className="mt-5 text-[28px] font-bold leading-none tracking-[-0.02em] text-ink">
          {t.meta.siteName}
        </h1>
        <p className="mt-3 text-sm text-ink-secondary">{t.auth.signInSubtitle}</p>
      </header>

      <div className="auth-card panel-glass mt-8 rounded-card p-6 sm:p-7">
        <div className="flex items-center gap-3">
          <h2 className="tech-label">{t.auth.signInHeading}</h2>
          <span aria-hidden className="auth-rule" />
        </div>

        {/* autoComplete off, and no placeholder: the field suggests nothing.
            The browser's stored-credential dropdown and its autofill tint were
            being read as the site hinting at an account name. */}
        <form className="mt-5" onSubmit={submit} noValidate autoComplete="off">
          <div className="mb-4">
            <Label htmlFor="identifier">{t.auth.identifier}</Label>
            <Input
              id="identifier"
              type="text"
              autoComplete="off"
              required
              className="font-mono"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
            />
          </div>

          <div className="mb-2">
            <Label htmlFor="password">{t.auth.password}</Label>
            {/* "new-password" rather than "off": the one value password
                managers actually honour as "do not offer saved logins here". */}
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              className="font-mono"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <FieldError>{error}</FieldError>

          <Button type="submit" size="lg" className="mt-5 w-full" disabled={busy}>
            {busy ? t.auth.signingIn : t.auth.signInButton}
          </Button>
        </form>

        {config?.google_oauth_enabled && (
          <>
            <div className="my-5 flex items-center gap-3">
              <span aria-hidden className="h-px flex-1 bg-line" />
              <span className="tech-label">{t.common.or}</span>
              <span aria-hidden className="h-px flex-1 bg-line" />
            </div>
            <a
              href={`${BROWSER_API_URL}/api/v1/auth/google/authorize`}
              className={cn(buttonVariants({ variant: 'outline', size: 'lg' }), 'w-full')}
            >
              {t.auth.google}
            </a>
          </>
        )}
      </div>

      {/* Self-registration is closed; accounts come from an administrator. */}
      <p className="mt-5 text-center text-xs leading-relaxed text-ink-muted">{t.auth.noSignUp}</p>
    </div>
  );
}

function LoginFallback() {
  const { t } = useI18n();
  return (
    <div className="auth-stage w-full max-w-[26rem] text-center text-sm text-ink-muted">
      {t.common.loading}
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFallback />}>
      <LoginForm />
    </Suspense>
  );
}
