/** @type {import('next').NextConfig} */
const nextConfig = {
  // Emits .next/standalone with a minimal node_modules, so the runtime image
  // stays small and needs no npm install.
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,
  eslint: { ignoreDuringBuilds: true },
  experimental: {
    // Shiki loads its grammars and themes lazily; keep it out of the bundler
    // so the standalone output resolves them from node_modules at runtime.
    serverComponentsExternalPackages: ['shiki', '@shikijs/rehype'],
  },
};

export default nextConfig;
