import rehypeSlug from 'rehype-slug';
import rehypeStringify from 'rehype-stringify';
import remarkDirective from 'remark-directive';
import remarkGfm from 'remark-gfm';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import { unified } from 'unified';
import { visit } from 'unist-util-visit';

import rehypeShiki from '@shikijs/rehype';

/**
 * Turns `:::tip` / `:::warning` / `:::exam-tip` container directives into
 * labelled callout divs.
 */
const CALLOUTS: Record<string, string> = {
  tip: 'Tip',
  warning: 'Warning',
  'exam-tip': 'Exam tip',
  note: 'Note',
};

function remarkCallouts() {
  return (tree: any) => {
    visit(tree, (node: any) => {
      if (node.type !== 'containerDirective') return;
      const label = CALLOUTS[node.name];
      if (!label) return;

      node.data ??= {};
      node.data.hName = 'div';
      node.data.hProperties = { className: ['callout', `callout-${node.name}`] };
      node.children.unshift({
        type: 'paragraph',
        data: { hName: 'span', hProperties: { className: ['callout-label'] } },
        children: [{ type: 'text', value: label }],
      });
    });
  };
}

/** Wraps every <pre> in a positioned container so a copy button can sit on it. */
function rehypeCodeBlockWrapper() {
  return (tree: any) => {
    visit(tree, 'element', (node: any, index: number | undefined, parent: any) => {
      if (node.tagName !== 'pre' || !parent || index === undefined) return;
      if (parent.type === 'element' && parent.properties?.className?.includes?.('code-block')) {
        return;
      }
      parent.children[index] = {
        type: 'element',
        tagName: 'div',
        properties: { className: ['code-block'] },
        children: [node],
      };
    });
  };
}

let processor: ReturnType<typeof buildProcessor> | null = null;

function buildProcessor() {
  return unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkDirective)
    .use(remarkCallouts)
    .use(remarkRehype)
    .use(rehypeSlug)
    // The plugin's overloads do not narrow inside a unified chain; Shiki
    // validates these options itself at runtime.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    .use(rehypeShiki as any, {
      themes: { light: 'github-light', dark: 'github-dark' },
      defaultColor: 'light',
      // Everything a CKA lesson realistically contains.
      langs: ['bash', 'shell', 'yaml', 'json', 'text', 'diff', 'ini', 'go'],
      fallbackLanguage: 'text',
    })
    .use(rehypeCodeBlockWrapper)
    .use(rehypeStringify);
}

/** Renders lesson markdown to HTML on the server (so it is indexable). */
export async function renderMarkdown(markdown: string): Promise<string> {
  processor ??= buildProcessor();
  const file = await processor.process(markdown);
  return String(file);
}
