'use client';

import { useState } from 'react';

/**
 * A plain, copyable code block for content that arrives as raw text at runtime
 * (lab setup, solutions, verification). Lesson markdown is highlighted on the
 * server instead - see lib/markdown.ts.
 */
export function CodeBlock({ code, language = 'bash' }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard unavailable - the text is selectable either way */
    }
  };

  return (
    <div className="code-block">
      <pre className="overflow-x-auto p-4 text-[0.85rem] leading-relaxed">
        <code className={`language-${language} font-mono text-ink-secondary`}>{code}</code>
      </pre>
      <button type="button" className="copy-button" onClick={copy} aria-label="Copy to clipboard">
        {copied ? 'Copied' : 'Copy'}
      </button>
    </div>
  );
}
