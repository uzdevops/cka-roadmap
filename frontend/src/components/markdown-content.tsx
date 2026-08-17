'use client';

import { useEffect, useRef } from 'react';

/**
 * Renders the server-highlighted lesson HTML and attaches a copy button to
 * every code block after mount. Rendering happens on the server so the content
 * is indexable; only the button is client-side.
 */
export function MarkdownContent({ html }: { html: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = ref.current;
    if (!root) return;

    const blocks = Array.from(root.querySelectorAll<HTMLElement>('.code-block'));
    const cleanups: (() => void)[] = [];

    for (const block of blocks) {
      if (block.querySelector('.copy-button')) continue;

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy-button';
      button.textContent = 'Copy';
      button.setAttribute('aria-label', 'Copy code to clipboard');

      const onClick = async () => {
        const code = block.querySelector('code')?.textContent ?? '';
        try {
          await navigator.clipboard.writeText(code);
          button.textContent = 'Copied';
        } catch {
          button.textContent = 'Press ⌘C';
        }
        window.setTimeout(() => {
          button.textContent = 'Copy';
        }, 1600);
      };

      button.addEventListener('click', onClick);
      block.appendChild(button);
      cleanups.push(() => {
        button.removeEventListener('click', onClick);
        button.remove();
      });
    }

    return () => cleanups.forEach((fn) => fn());
  }, [html]);

  return (
    <div
      ref={ref}
      className="prose-lesson max-w-prose"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
