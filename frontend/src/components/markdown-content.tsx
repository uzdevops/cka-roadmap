'use client';

import { useEffect, useRef } from 'react';

import { useI18n } from '@/i18n/provider';

/** `title="pod.yaml"`, `filename=pod.yaml` - an explicit name beats the language. */
const FILE_META = /\b(?:title|filename|file)\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s}]+))/;

/** The first word of a fence info string, e.g. `yaml` out of `yaml {1,3}`. */
const LANG = /^[A-Za-z0-9+#._-]+/;

interface Chip {
  text: string;
  /** A filename keeps its own casing; a language reads as an uppercase label. */
  file: boolean;
}

function fenceChip(info: string | undefined): Chip | null {
  const trimmed = (info ?? '').trim();
  if (!trimmed) return null;

  const named = FILE_META.exec(trimmed);
  const file = named?.[1] ?? named?.[2] ?? named?.[3];
  if (file) return { text: file, file: true };

  const lang = LANG.exec(trimmed)?.[0];
  return lang ? { text: lang, file: false } : null;
}

/**
 * Whatever language the rendered markup still carries, if any.
 *
 * Shiki replaces the whole `<pre>` and `@shikijs/rehype` leaves its
 * `addLanguageClass` option off, so today this finds nothing - it is the
 * fallback for the day that changes, and for blocks the source scan could not
 * be matched to.
 */
function domLanguage(block: HTMLElement): string {
  const nodes = [block.querySelector('pre'), block.querySelector('code')];
  for (const el of nodes) {
    if (!el) continue;
    const attr = el.getAttribute('data-language') ?? el.getAttribute('data-lang');
    if (attr) return attr;
    const cls = Array.from(el.classList).find((c) => c.startsWith('language-'));
    if (cls) return cls.slice('language-'.length);
  }
  return '';
}

/**
 * Renders the server-highlighted lesson HTML and decorates every code block
 * after mount: a mono language (or filename) chip in a header strip, plus the
 * copy button, which stays hidden until the block is hovered or focused.
 * Rendering happens on the server so the content is indexable; only the
 * controls are client-side.
 *
 * `codeInfo` carries the fence info strings from the source markdown, in
 * document order, because the highlighted HTML no longer contains them. They
 * are used only when they line up one-to-one with the rendered blocks - an
 * unfenced (indented) block would shift every label after it, and a wrong
 * language is worse than no chip at all.
 */
export function MarkdownContent({
  html,
  codeInfo = [],
}: {
  html: string;
  codeInfo?: string[];
}) {
  const { t } = useI18n();
  const ref = useRef<HTMLDivElement>(null);

  const copy = t.lessons.copy;
  const copied = t.lessons.copied;
  const copyManual = t.lessons.copyManual;
  const copyLabel = t.lessons.copyLabel;
  // A fence info string never contains a newline, so this round-trips exactly
  // and gives the effect a stable dependency instead of a fresh array.
  const infoKey = codeInfo.join('\n');

  useEffect(() => {
    const root = ref.current;
    if (!root) return;

    const blocks = Array.from(root.querySelectorAll<HTMLElement>('.code-block'));
    const info = infoKey.length > 0 ? infoKey.split('\n') : [];
    const aligned = info.length === blocks.length ? info : null;
    const cleanups: (() => void)[] = [];

    blocks.forEach((block, i) => {
      if (block.querySelector('.copy-button')) return;

      const chip = fenceChip(aligned?.[i] ?? domLanguage(block));
      if (chip) {
        const head = document.createElement('div');
        head.className = 'lsnd-code-head';

        const label = document.createElement('span');
        label.className = chip.file
          ? 'tech-label lsnd-code-chip lsnd-code-chip-file'
          : 'tech-label lsnd-code-chip';
        label.textContent = chip.text;

        head.appendChild(label);
        block.classList.add('lsnd-code-titled');
        block.insertBefore(head, block.firstChild);

        cleanups.push(() => {
          head.remove();
          block.classList.remove('lsnd-code-titled');
        });
      }

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy-button';
      button.textContent = copy;
      button.setAttribute('aria-label', copyLabel);

      const onClick = async () => {
        const code = block.querySelector('code')?.textContent ?? '';
        try {
          await navigator.clipboard.writeText(code);
          button.textContent = copied;
        } catch {
          button.textContent = copyManual;
        }
        window.setTimeout(() => {
          button.textContent = copy;
        }, 1600);
      };

      button.addEventListener('click', onClick);
      block.appendChild(button);
      cleanups.push(() => {
        button.removeEventListener('click', onClick);
        button.remove();
      });
    });

    return () => cleanups.forEach((fn) => fn());
  }, [html, infoKey, copy, copied, copyManual, copyLabel]);

  return (
    <div
      ref={ref}
      className="prose-lesson max-w-prose"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
