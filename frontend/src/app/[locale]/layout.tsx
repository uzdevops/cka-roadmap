import type { Metadata } from 'next';
import { IBM_Plex_Mono, Space_Grotesk } from 'next/font/google';
import { notFound } from 'next/navigation';

import { AppShell } from '@/components/app-shell';
import { ThemeScript } from '@/components/theme-toggle';
import { getDictionary } from '@/i18n';
import { isLocale, LOCALES, type Locale } from '@/i18n/config';
import { I18nProvider } from '@/i18n/provider';
import { AuthProvider } from '@/lib/auth-context';

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

// Self-hosted by next/font at build time: no network call from the browser and
// no layout shift. Exposed as CSS variables so globals.css stays the single
// source of truth for typography as well as colour.
const sans = Space_Grotesk({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-sans',
  display: 'swap',
});

const mono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-mono',
  display: 'swap',
});

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const locale = isLocale(params.locale) ? params.locale : 'en';
  const t = getDictionary(locale);

  return {
    metadataBase: new URL(siteUrl),
    title: { default: t.meta.titleDefault, template: `%s | ${t.meta.siteName}` },
    description: t.meta.description,
    keywords: [
      'CKA',
      'Kubernetes',
      'Certified Kubernetes Administrator',
      'kubectl',
      locale === 'uz' ? 'imtihonga tayyorgarlik' : 'exam preparation',
    ],
    alternates: {
      canonical: `/${locale}`,
      // hreflang, so each language is indexed under its own URL.
      languages: Object.fromEntries(LOCALES.map((l) => [l, `/${l}`])),
    },
    openGraph: {
      type: 'website',
      siteName: t.meta.siteName,
      title: t.meta.titleDefault,
      description: t.meta.description,
      url: `${siteUrl}/${locale}`,
      locale: locale === 'uz' ? 'uz_UZ' : 'en_US',
    },
    twitter: { card: 'summary_large_image' },
    robots: { index: true, follow: true },
  };
}

export default function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  if (!isLocale(params.locale)) notFound();
  const locale = params.locale as Locale;

  return (
    <html lang={locale} className={`${sans.variable} ${mono.variable}`} suppressHydrationWarning>
      <head>
        <ThemeScript />
      </head>
      <body className="min-h-screen antialiased">
        <I18nProvider locale={locale}>
          <AuthProvider>
            <AppShell>{children}</AppShell>
          </AuthProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
