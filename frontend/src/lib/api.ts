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
   Browser-side fetching, with token refresh
   -------------------------------------------------------------------------- */

export const ACCESS_COOKIE = 'cka.access_token';
export const REFRESH_COOKIE = 'cka.refresh_token';

/**
 * Tokens live in cookies rather than localStorage.
 *
 * Nothing on this platform is public any more, and the gate that enforces that
 * is `middleware.ts` - which runs on the server and can only read cookies.
 * Server-rendered pages need them for the same reason: they fetch lesson and
 * roadmap content from an API that now refuses anonymous callers.
 *
 * These are readable by JavaScript, exactly as localStorage was, so this is not
 * a change in exposure. Making them HttpOnly would be a real improvement, but
 * it needs the API to accept a cookie instead of a bearer header.
 */
function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${name.replace(/\./g, '\\.')}=([^;]*)`),
  );
  return match ? decodeURIComponent(match[1]) : null;
}

function writeCookie(name: string, value: string, maxAgeSeconds: number): void {
  const secure = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie =
    `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAgeSeconds}` +
    `; SameSite=Lax${secure}`;
}

// Long enough that the cookie outlives the access token it carries: an expired
// access token is refreshed on the first 401, but only if it is still here to
// be sent.
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30;

export const tokenStore = {
  get access(): string | null {
    return readCookie(ACCESS_COOKIE);
  },
  get refresh(): string | null {
    return readCookie(REFRESH_COOKIE);
  },
  set(access: string, refresh: string) {
    writeCookie(ACCESS_COOKIE, access, COOKIE_MAX_AGE);
    writeCookie(REFRESH_COOKIE, refresh, COOKIE_MAX_AGE);
    window.dispatchEvent(new Event('cka:auth-changed'));
  },
  clear() {
    writeCookie(ACCESS_COOKIE, '', 0);
    writeCookie(REFRESH_COOKIE, '', 0);
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
