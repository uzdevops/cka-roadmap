'use client';

import { useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

const STORAGE_KEY = 'cka.theme';

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  if (theme === 'system') {
    root.removeAttribute('data-theme');
    root.classList.remove('dark');
  } else {
    root.setAttribute('data-theme', theme);
    root.classList.toggle('dark', theme === 'dark');
  }
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>('system');

  useEffect(() => {
    const stored = (window.localStorage.getItem(STORAGE_KEY) as Theme | null) ?? 'system';
    setTheme(stored);
    applyTheme(stored);
  }, []);

  const cycle = () => {
    const next: Theme = theme === 'system' ? 'light' : theme === 'light' ? 'dark' : 'system';
    setTheme(next);
    window.localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  };

  const icon = theme === 'light' ? '☀' : theme === 'dark' ? '☾' : '◐';

  return (
    <button
      type="button"
      onClick={cycle}
      title={`Theme: ${theme}. Click to change.`}
      aria-label={`Theme: ${theme}. Click to change.`}
      className="flex h-9 w-9 items-center justify-center rounded-lg border border-line text-ink-secondary transition-colors hover:bg-[var(--surface-2)] hover:text-ink"
    >
      <span aria-hidden className="text-base leading-none">
        {icon}
      </span>
    </button>
  );
}

/**
 * Applies the stored theme before first paint, so a dark-mode user never sees
 * a light flash. Rendered as an inline script in the document head.
 */
export function ThemeScript() {
  const code = `(function(){try{var t=localStorage.getItem('${STORAGE_KEY}');if(t&&t!=='system'){document.documentElement.setAttribute('data-theme',t);if(t==='dark')document.documentElement.classList.add('dark');}else if(window.matchMedia('(prefers-color-scheme: dark)').matches){document.documentElement.classList.add('dark');}}catch(e){}})();`;
  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}
