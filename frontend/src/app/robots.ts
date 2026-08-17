import type { MetadataRoute } from 'next';

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      // Locale-prefixed, so the private areas are blocked in every language.
      disallow: [
        '/*/admin',
        '/*/dashboard',
        '/*/profile',
        '/*/auth/callback',
        '/healthz',
        '/readyz',
        '/api/',
      ],
    },
    sitemap: `${siteUrl}/sitemap.xml`,
  };
}
