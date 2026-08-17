import type { MetadataRoute } from 'next';

/**
 * Nothing here is public any more: every page sits behind the login gate in
 * `middleware.ts`, so there is nothing for a crawler to index and no sitemap to
 * point it at. A crawler would only ever see the login screen.
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      disallow: '/',
    },
  };
}
