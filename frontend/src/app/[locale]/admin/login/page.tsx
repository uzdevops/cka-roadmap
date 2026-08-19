'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';

import { BrandMark } from '@/components/brand-mark';
import { NavIcon } from '@/components/nav-icons';
import { Button } from '@/components/ui/button';
import { FieldError, Input, Label } from '@/components/ui/field';
import { useI18n } from '@/i18n/provider';
import { useAuth } from '@/lib/auth-context';

/**
 * The console's door - /admin/login.
 *
 * The student sign-in and this one used to be the same screen, which meant an
 * administrator could not tell which surface they were entering until after
 * they were in. So the door borrows the console's own language: the flat
 * tinted ground with the aurora and dot grid switched off (`.adm-auth` in
 * globals.css), the ADMIN AREA tag spelled out above the form, and an opaque
 * card where the student one is glass.
 *
 * The form itself stays the same two fields against the same endpoint - which
 * account is an administrator is the server's decision, not this page's. The
 * only thing decided here is where success lands: the console. A student who
 * signs in at this door is caught by the console's own guard, with a way back.
 */
function AdminLoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { login } = useAuth();
  const { t, href } = useI18n();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const next = href(params.get('next') ?? '/admin');

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
    <div className="adm-auth auth-stage w-full max-w-[26rem]">
      <header className="flex flex-col items-center text-center">
        {/* Same tile as the student door, one size down: this room is denser. */}
        <span aria-hidden className="auth-mark brand-tile">
          <BrandMark size={40} />
        </span>
        <h1 className="mt-4 text-2xl font-bold leading-none tracking-[-0.02em] text-ink">
          {t.meta.siteName}
        </h1>
        {/* The identity is spelled out, not implied by the tint - the same tag
            the console header wears. */}
        <span className="adm-tag mt-4">
          <NavIcon name="admin" size={12} />
          {t.admin.consoleTag}
        </span>
        <p className="mt-3 text-sm text-ink-secondary">{t.auth.adminSignInSubtitle}</p>
      </header>

      <div className="adm-auth-card mt-8 rounded-card p-6 sm:p-7">
        <div className="flex items-center gap-3">
          <h2 className="tech-label">{t.admin.consoleTitle}</h2>
          <span aria-hidden className="auth-rule" />
        </div>

        <form className="mt-5" onSubmit={submit} noValidate>
          <div className="mb-4">
            <Label htmlFor="identifier">{t.auth.identifier}</Label>
            {/* Not type="email": the admin signs in as `admin`, and the browser
                would refuse to submit that against an email input. */}
            <Input
              id="identifier"
              type="text"
              autoComplete="username"
              required
              className="font-mono"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder={t.auth.identifierPlaceholder}
            />
          </div>

          <div className="mb-2">
            <Label htmlFor="password">{t.auth.password}</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              className="font-mono"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          <FieldError>{error}</FieldError>

          <Button type="submit" size="lg" className="mt-5 w-full" disabled={busy}>
            {busy ? t.auth.signingIn : t.auth.signInButton}
          </Button>
        </form>
      </div>

      {/* The deliberate way back, mirroring the console header's exit. */}
      <p className="mt-5 text-center text-xs leading-relaxed text-ink-muted">
        <Link href={href('/login')} className="transition-colors hover:text-ink">
          ← {t.auth.studentSignIn}
        </Link>
      </p>
    </div>
  );
}

function AdminLoginFallback() {
  const { t } = useI18n();
  return (
    <div className="adm-auth auth-stage w-full max-w-[26rem] text-center text-sm text-ink-muted">
      {t.common.loading}
    </div>
  );
}

export default function AdminLoginPage() {
  return (
    <Suspense fallback={<AdminLoginFallback />}>
      <AdminLoginForm />
    </Suspense>
  );
}
