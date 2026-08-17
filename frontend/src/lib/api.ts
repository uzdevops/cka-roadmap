/**
 * API client.
 *
 * Two base URLs on purpose: the browser reaches the API through the published
 * host port, while server-side rendering talks to the backend container over
 * the compose network.
 */

import { DEFAULT_LOCALE, type Locale } from '@/i18n/config';

const API_V1 = '/api/v1';

/**
 * Locale used for browser-side requests. The I18nProvider sets it from the URL
 * segment on mount, so individual call sites never have to pass it.
 */
let activeLocale: Locale = DEFAULT_LOCALE;

export function setApiLocale(locale: Locale): void {
  activeLocale = locale;
}

/** Appends ?lang= without clobbering an existing query string. */
function withLocale(path: string, locale: Locale): string {
  const separator = path.includes('?') ? '&' : '?';
  return `${path}${separator}lang=${locale}`;
}

export const BROWSER_API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export function serverApiUrl(): string {
  return process.env.INTERNAL_API_URL ?? BROWSER_API_URL;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly detail?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function extractDetail(body: unknown): string | null {
  if (!body || typeof body !== 'object') return null;
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string; loc?: unknown[] };
    if (first?.msg) {
      const field = Array.isArray(first.loc) ? first.loc.at(-1) : undefined;
      return field ? `${String(field)}: ${first.msg}` : first.msg;
    }
  }
  return null;
}

/* --------------------------------------------------------------------------
   Server-side fetching (public content only - no auth header)
   -------------------------------------------------------------------------- */

export async function serverFetch<T>(
  path: string,
  locale: Locale = DEFAULT_LOCALE,
): Promise<T | null> {
  const url = `${serverApiUrl()}${API_V1}${withLocale(path, locale)}`;
  try {
    // Always live: the backend is not reachable during the image build, so a
    // prerendered page would bake in an empty state permanently. Pages using
    // this also set `export const dynamic = 'force-dynamic'`.
    const res = await fetch(url, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    // The backend may be briefly unavailable during a restart; pages that use
    // this render an empty state rather than a 500.
    return null;
  }
}

/* --------------------------------------------------------------------------
   Browser-side fetching, with token refresh
   -------------------------------------------------------------------------- */

const ACCESS_KEY = 'cka.access_token';
const REFRESH_KEY = 'cka.refresh_token';

export const tokenStore = {
  get access(): string | null {
    if (typeof window === 'undefined') return null;
    return window.localStorage.getItem(ACCESS_KEY);
  },
  get refresh(): string | null {
    if (typeof window === 'undefined') return null;
    return window.localStorage.getItem(REFRESH_KEY);
  },
  set(access: string, refresh: string) {
    window.localStorage.setItem(ACCESS_KEY, access);
    window.localStorage.setItem(REFRESH_KEY, refresh);
    window.dispatchEvent(new Event('cka:auth-changed'));
  },
  clear() {
    window.localStorage.removeItem(ACCESS_KEY);
    window.localStorage.removeItem(REFRESH_KEY);
    window.dispatchEvent(new Event('cka:auth-changed'));
  },
};

let refreshInFlight: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const refresh = tokenStore.refresh;
  if (!refresh) return false;

  // Collapse concurrent 401s into a single refresh request.
  refreshInFlight ??= (async () => {
    try {
      const res = await fetch(`${BROWSER_API_URL}${API_V1}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) {
        tokenStore.clear();
        return false;
      }
      const data = await res.json();
      tokenStore.set(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
  signal?: AbortSignal;
}

export async function apiFetch<T>(
  path: string,
  { method = 'GET', body, auth = true, signal }: RequestOptions = {},
): Promise<T> {
  const send = async (token: string | null): Promise<Response> => {
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (token) headers.Authorization = `Bearer ${token}`;

    return fetch(`${BROWSER_API_URL}${API_V1}${withLocale(path, activeLocale)}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  };

  let res = await send(auth ? tokenStore.access : null);

  if (res.status === 401 && auth && tokenStore.refresh) {
    if (await refreshTokens()) {
      res = await send(tokenStore.access);
    }
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const payload = text ? JSON.parse(text) : null;

  if (!res.ok) {
    throw new ApiError(
      res.status,
      extractDetail(payload) ?? `Request failed with status ${res.status}`,
      payload,
    );
  }

  return payload as T;
}

/** Public GET that works before the user has signed in. */
export function apiPublic<T>(path: string): Promise<T> {
  return apiFetch<T>(path, { auth: !!tokenStore.access });
}
