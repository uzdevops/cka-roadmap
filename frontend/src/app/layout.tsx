import './globals.css';

/**
 * Passthrough root layout.
 *
 * `<html>` and `<body>` live in `[locale]/layout.tsx`, because the `lang`
 * attribute has to follow the URL's locale segment. Route handlers
 * (`/healthz`, `/readyz`, `/api/*`) and the metadata files bypass layouts
 * entirely, so nothing else needs a document shell.
 */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return children;
}
