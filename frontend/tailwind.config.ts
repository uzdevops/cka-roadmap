import type { Config } from 'tailwindcss';

/**
 * Colours are declared once as CSS custom properties in globals.css and only
 * referenced here, so light/dark swap in a single place and the chart code and
 * the UI draw from the same validated tokens.
 */
const config: Config = {
  darkMode: 'class',
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        plane: 'var(--plane)',
        surface: 'var(--surface-1)',
        'surface-2': 'var(--surface-2)',
        ink: {
          DEFAULT: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted: 'var(--text-muted)',
        },
        line: 'var(--border)',
        grid: 'var(--grid)',
        axis: 'var(--axis)',
        accent: {
          DEFAULT: 'var(--accent)',
          ink: 'var(--accent-ink)',
        },
        track: 'var(--track)',
        good: 'var(--good)',
        warning: 'var(--warning)',
        serious: 'var(--serious)',
        critical: 'var(--critical)',
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      borderRadius: {
        card: '12px',
      },
      maxWidth: {
        prose: '72ch',
      },
    },
  },
  plugins: [],
};

export default config;
