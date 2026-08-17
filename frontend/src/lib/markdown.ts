import rehypeSlug from 'rehype-slug';
import rehypeStringify from 'rehype-stringify';
import remarkDirective from 'remark-directive';
import remarkGfm from 'remark-gfm';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import { unified } from 'unified';
import { visit } from 'unist-util-visit';

import rehypeShiki from '@shikijs/rehype';

import { getDictionary } from '@/i18n';
import { DEFAULT_LOCALE, type Locale } from '@/i18n/config';
import { archAnchor, archComponent, buildArchitectureDiagram } from '@/lib/architecture';

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

/**
 * `::cluster-architecture` expands to the clickable control-plane / worker
 * diagram. Its boxes link to the `:::component{key=…}` rows below it, so the
 * two directives are always authored as a pair.
 */
function remarkArchitectureDiagram(locale: Locale) {
  const t = getDictionary(locale);
  return (tree: any) => {
    visit(tree, (node: any) => {
      if (node.type !== 'leafDirective' || node.name !== 'cluster-architecture') return;

      const figure = buildArchitectureDiagram({ caption: t.architecture.caption });

      node.data ??= {};
      node.data.hName = figure.tagName;
      node.data.hProperties = figure.properties;
      node.data.hChildren = figure.children;
    });
  };
}

/**
 * `:::component{key=etcd}` wraps an explanation in a row the diagram can jump
 * to. The anchor comes from `key`, not from the heading text, because headings
 * are translated per locale - a slug-derived anchor would break in Uzbek. The
 * component name is a proper noun, so the row renders it itself rather than
 * making every translation repeat it.
 */
function remarkComponentRows() {
  return (tree: any) => {
    visit(tree, (node: any) => {
      if (node.type !== 'containerDirective' || node.name !== 'component') return;

      const key = node.attributes?.key;
      const component = key ? archComponent(key) : undefined;
      if (!component) return;

      node.data ??= {};
      node.data.hName = 'div';
      node.data.hProperties = {
        id: archAnchor(component.key),
        className: [
          'arch-row',
          `arch-tone-${component.tone}`,
          // The two groupings lead the components inside them, so they read as
          // section headers rather than as a fourth sibling in the list.
          ...(component.kind === 'plane' ? ['arch-row-plane'] : []),
        ],
        // `:target` styling is the only feedback that the jump landed, so give
        // assistive tech the same grouping.
        role: 'group',
        'aria-labelledby': `${archAnchor(component.key)}-name`,
      };
      node.children.unshift({
        type: 'paragraph',
        data: { hName: 'div', hProperties: { className: ['arch-row-head'] } },
        children: [
          {
            type: 'text',
            value: component.name,
            data: {
              hName: 'span',
              hProperties: {
                id: `${archAnchor(component.key)}-name`,
                className: ['arch-row-name'],
              },
            },
          },
        ],
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

// The diagram's labels come from the dictionary, so the processor is per locale.
const processors = new Map<Locale, ReturnType<typeof buildProcessor>>();

function buildProcessor(locale: Locale) {
  return unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkDirective)
    .use(remarkCallouts)
    .use(remarkComponentRows)
    .use(remarkArchitectureDiagram, locale)
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
export async function renderMarkdown(
  markdown: string,
  locale: Locale = DEFAULT_LOCALE,
): Promise<string> {
  let processor = processors.get(locale);
  if (!processor) {
    processor = buildProcessor(locale);
    processors.set(locale, processor);
  }
  const file = await processor.process(markdown);
  return String(file);
}
