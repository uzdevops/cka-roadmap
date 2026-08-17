'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect } from 'react';

import { useI18n } from '@/i18n/provider';
import { useAuth } from '@/lib/auth-context';

/** Receives the token pair the backend appends after a Google OAuth exchange. */
function CallbackHandler() {
  const params = useSearchParams();
  const router = useRouter();
  const { applyTokens } = useAuth();
  const { t, href } = useI18n();

  useEffect(() => {
    const access = params.get('access_token');
    const refresh = params.get('refresh_token');

    if (!access || !refresh) {
      router.replace(href('/login?error=oauth'));
      return;
    }

    void applyTokens({ access_token: access, refresh_token: refresh, token_type: 'bearer' }).then(
      () => router.replace(href('/dashboard')),
    );
  }, [params, router, applyTokens, href]);

  return (
    <div className="py-24 text-center text-sm text-ink-secondary">{t.auth.completing}</div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<div className="py-24 text-center text-ink-muted" />}>
      <CallbackHandler />
    </Suspense>
  );
}
