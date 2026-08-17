/**
 * The clickable cluster-architecture diagram used by the `::cluster-architecture`
 * markdown directive, plus the component registry its `:::component{key=…}`
 * rows share.
 *
 * Two constraints shape this file:
 *
 * 1. The markdown pipeline has no `rehype-raw`, so nothing here may be an HTML
 *    string - the diagram is built as a hast tree that remark-rehype passes
 *    straight through.
 * 2. Anchors are derived from `key`, never from heading text. Lesson headings
 *    are translated per locale, so slug-derived anchors would break the moment
 *    the page is read in Uzbek.
 *
 * Colour is identity only, never the sole carrier of meaning: every box states
 * its own name, and the palette matches the `--series-*` slots the charts use.
 */

// --- hast helpers ----------------------------------------------------------

export interface HastText {
  type: 'text';
  value: string;
}

export interface HastElement {
  type: 'element';
  tagName: string;
  properties: Record<string, unknown>;
  children: (HastElement | HastText)[];
}

type Child = HastElement | HastText;

const txt = (value: string): HastText => ({ type: 'text', value });

const el = (
  tagName: string,
  properties: Record<string, unknown> = {},
  children: Child[] = [],
): HastElement => ({ type: 'element', tagName, properties, children });

// --- component registry ----------------------------------------------------

/** Palette slot used for a component's outline in the diagram and its row chip. */
export type ArchTone = '1' | '2' | '3' | '4' | '5' | '6' | 'neutral';

export interface ArchComponent {
  /** Stable anchor key. Also what `:::component{key=…}` refers to. */
  key: string;
  /** Proper nouns - identical in every locale, so they are never translated. */
  name: string;
  tone: ArchTone;
  /**
   * `plane` is one of the two headline groupings rather than a single process,
   * so its row leads the components that sit inside it.
   */
  kind: 'plane' | 'component';
}

/** Every clickable node in the diagram, in the order its rows should be read. */
export const ARCH_COMPONENTS: ArchComponent[] = [
  { key: 'control-plane', name: 'Control Plane', tone: '5', kind: 'plane' },
  { key: 'kube-apiserver', name: 'API Server', tone: '1', kind: 'component' },
  { key: 'etcd', name: 'etcd', tone: '6', kind: 'component' },
  { key: 'kube-controller-manager', name: 'Controller Manager', tone: '5', kind: 'component' },
  { key: 'kube-scheduler', name: 'Scheduler', tone: '4', kind: 'component' },
  { key: 'worker', name: 'Worker', tone: '3', kind: 'plane' },
  { key: 'kubelet', name: 'Kubelet', tone: '3', kind: 'component' },
  { key: 'kube-proxy', name: 'Kube-proxy', tone: '2', kind: 'component' },
  { key: 'container-runtime', name: 'Container Runtime', tone: 'neutral', kind: 'component' },
];

export function archComponent(key: string): ArchComponent | undefined {
  return ARCH_COMPONENTS.find((component) => component.key === key);
}

/** `etcd` -> `arch-etcd`. Prefixed so it cannot collide with a heading slug. */
export function archAnchor(key: string): string {
  return `arch-${key}`;
}

// --- geometry --------------------------------------------------------------

const VIEW_W = 860;
const VIEW_H = 524;

/** Second worker node is the first one shifted straight down. */
const WORKER_GAP = 224;

interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

const CONTROL_PLANE: Box = { x: 16, y: 76, w: 436, h: 432 };
const ETCD: Box = { x: 40, y: 122, w: 224, h: 98 };
const API_SERVER: Box = { x: 316, y: 168, w: 116, h: 196 };
const CONTROLLER_MANAGER: Box = { x: 36, y: 300, w: 232, h: 46 };
const SCHEDULER: Box = { x: 56, y: 400, w: 184, h: 46 };

const WORKER: Box = { x: 596, y: 76, w: 248, h: 190 };
const KUBE_PROXY: Box = { x: 620, y: 98, w: 136, h: 38 };
const KUBELET: Box = { x: 620, y: 152, w: 112, h: 38 };
const RUNTIME: Box = { x: 620, y: 212, w: 200, h: 36 };

const shift = (box: Box, dy: number): Box => ({ ...box, y: box.y + dy });

/** ~0.35em of the label size: puts the cap height, not the baseline, on centre. */
const LABEL_BASELINE = 5.25;
const PILL_BASELINE = 6;

// --- primitives ------------------------------------------------------------

/**
 * A clickable component box: rounded rect plus centred label, wrapped in an
 * SVG `<a>`. The visible label is the link's accessible name, so no aria-label
 * is needed - and none could be written here anyway, since this file has no
 * locale.
 */
function componentBox(key: string, box: Box, lines: string[]): HastElement {
  const component = archComponent(key);
  if (!component) throw new Error(`Unknown architecture component: ${key}`);

  const cx = box.x + box.w / 2;
  const cy = box.y + box.h / 2;
  // Multi-line labels are centred as a block: first line lifted by half the
  // total leading, each subsequent line one line-height below. The baseline is
  // nudged by hand rather than with `dominant-baseline`, whose support across
  // renderers is uneven enough that centring would silently differ.
  const leading = 15;
  const top = cy - ((lines.length - 1) * leading) / 2 + LABEL_BASELINE;

  return el(
    'a',
    { href: `#${archAnchor(key)}`, className: ['arch-link'] },
    [
      el('rect', {
        x: box.x,
        y: box.y,
        width: box.w,
        height: box.h,
        rx: 7,
        className: ['arch-node', `arch-tone-${component.tone}`],
      }),
      el(
        'text',
        {
          x: cx,
          y: top,
          textAnchor: 'middle',
          className: ['arch-node-label'],
        },
        lines.map((line, index) =>
          el('tspan', { x: cx, dy: index === 0 ? 0 : leading }, [txt(line)]),
        ),
      ),
    ],
  );
}

/** Plain (non-interactive) container: the control plane and worker outlines. */
function planeBox(box: Box, className: string): HastElement {
  return el('rect', {
    x: box.x,
    y: box.y,
    width: box.w,
    height: box.h,
    rx: 8,
    className: ['arch-plane', className],
  });
}

/**
 * The header pill above each plane. Clickable like every other box: the two
 * groupings have rows of their own, because "what is a control plane" is the
 * question that comes before any of the four processes inside it.
 */
function planePill(key: string, box: Box): HastElement {
  const plane = archComponent(key);
  if (!plane) throw new Error(`Unknown architecture plane: ${key}`);

  return el('a', { href: `#${archAnchor(key)}`, className: ['arch-link'] }, [
    el('rect', {
      x: box.x,
      y: box.y,
      width: box.w,
      height: box.h,
      rx: 8,
      className: ['arch-pill', `arch-tone-${plane.tone}`],
    }),
    el(
      'text',
      {
        x: box.x + box.w / 2,
        y: box.y + box.h / 2 + PILL_BASELINE,
        textAnchor: 'middle',
        className: ['arch-pill-label'],
      },
      [txt(plane.name)],
    ),
  ]);
}

/** One etcd member, drawn as the usual stacked-disc database glyph. */
function etcdMember(x: number, y: number): HastElement {
  const rx = 21;
  const ry = 7;
  const bodyTop = y + ry;
  const bodyHeight = 40;

  return el('g', { className: ['arch-etcd-member'] }, [
    // Barrel: straight sides closed by the bottom ellipse.
    el('path', {
      d: `M ${x - rx} ${bodyTop} v ${bodyHeight} a ${rx} ${ry} 0 0 0 ${rx * 2} 0 v -${bodyHeight} z`,
      className: ['arch-etcd-body'],
    }),
    el('ellipse', { cx: x, cy: bodyTop, rx, ry, className: ['arch-etcd-cap'] }),
    // Two dividers so it reads as stacked storage rather than a cylinder.
    el('path', {
      d: `M ${x - rx} ${bodyTop + 13} a ${rx} ${ry} 0 0 0 ${rx * 2} 0`,
      className: ['arch-etcd-rib'],
    }),
    el('path', {
      d: `M ${x - rx} ${bodyTop + 26} a ${rx} ${ry} 0 0 0 ${rx * 2} 0`,
      className: ['arch-etcd-rib'],
    }),
  ]);
}

/** etcd is a cluster, so its box holds three members and is one link. */
function etcdCluster(): HastElement {
  const members = [0, 1, 2].map((index) =>
    etcdMember(ETCD.x + 56 + index * 56, ETCD.y + 12),
  );

  return el('a', { href: `#${archAnchor('etcd')}`, className: ['arch-link'] }, [
    el('rect', {
      x: ETCD.x,
      y: ETCD.y,
      width: ETCD.w,
      height: ETCD.h,
      rx: 7,
      className: ['arch-node', 'arch-tone-6'],
    }),
    ...members,
    el(
      'text',
      {
        x: ETCD.x + ETCD.w / 2,
        y: ETCD.y + ETCD.h - 11,
        textAnchor: 'middle',
        className: ['arch-node-label'],
      },
      [txt('etcd')],
    ),
  ]);
}

/**
 * An arrow between two points. `tone` picks both the stroke colour and the
 * matching arrowhead marker.
 */
function arrow(
  from: [number, number],
  to: [number, number],
  tone: ArchTone,
  options: { both?: boolean } = {},
): HastElement {
  return el('path', {
    d: `M ${from[0]} ${from[1]} L ${to[0]} ${to[1]}`,
    className: ['arch-arrow', `arch-tone-${tone}`],
    markerEnd: `url(#arch-head-${tone})`,
    ...(options.both ? { markerStart: `url(#arch-head-${tone})` } : {}),
  });
}

/** One arrowhead marker per tone; CSS fills them from the same token. */
function arrowheads(): HastElement {
  const tones: ArchTone[] = ['1', '2', '3', '4', '5', '6', 'neutral'];
  return el(
    'defs',
    {},
    tones.map((tone) =>
      el(
        'marker',
        {
          id: `arch-head-${tone}`,
          viewBox: '0 0 10 10',
          refX: 8,
          refY: 5,
          markerWidth: 6,
          markerHeight: 6,
          orient: 'auto-start-reverse',
        },
        [
          el('path', {
            d: 'M 0 0 L 10 5 L 0 10 z',
            className: ['arch-head', `arch-tone-${tone}`],
          }),
        ],
      ),
    ),
  );
}

// --- the diagram -----------------------------------------------------------

/**
 * One worker node: the box, its three components, and its arrows. `index` also
 * decides where on the API server's right edge this node's two arrows land, so
 * the four of them stay spread out and inside the box.
 */
function workerNode(index: number): HastElement {
  const dy = index * WORKER_GAP;
  const box = shift(WORKER, dy);
  const proxy = shift(KUBE_PROXY, dy);
  const kubelet = shift(KUBELET, dy);
  const runtime = shift(RUNTIME, dy);

  // Both agents are clients of the API server; only the kubelet drives the
  // runtime. Those three arrows are the whole point of the worker half.
  const apiRight = API_SERVER.x + API_SERVER.w;
  const edge = (fraction: number): [number, number] => [
    apiRight + 4,
    API_SERVER.y + API_SERVER.h * fraction,
  ];
  const proxyTarget = edge(index === 0 ? 0.16 : 0.62);
  const kubeletTarget = edge(index === 0 ? 0.36 : 0.84);

  return el('g', {}, [
    planeBox(box, 'arch-plane-worker'),
    arrow([proxy.x - 6, proxy.y + proxy.h / 2], proxyTarget, '2'),
    arrow([kubelet.x - 6, kubelet.y + kubelet.h / 2], kubeletTarget, '3'),
    arrow(
      [kubelet.x + 40, kubelet.y + kubelet.h + 2],
      [runtime.x + 60, runtime.y - 4],
      '3',
    ),
    componentBox('kube-proxy', proxy, ['Kube-proxy']),
    componentBox('kubelet', kubelet, ['Kubelet']),
    componentBox('container-runtime', runtime, ['Container Runtime']),
  ]);
}

/**
 * Builds the whole diagram as a `<figure>`. The caption is supplied by the
 * caller because this module has no locale of its own; every box label is a
 * proper noun and comes from the registry.
 *
 * Child order is also tab order, so it runs Control Plane -> its four
 * components -> Worker -> its three, matching the rows underneath.
 */
export function buildArchitectureDiagram(labels: { caption: string }): HastElement {
  const svg = el(
    'svg',
    {
      viewBox: `0 0 ${VIEW_W} ${VIEW_H}`,
      className: ['arch-svg'],
      role: 'group',
      'aria-label': labels.caption,
    },
    [
      arrowheads(),

      // --- control plane ---
      planeBox(CONTROL_PLANE, 'arch-plane-control'),
      planePill('control-plane', { x: 16, y: 14, w: 300, h: 46 }),

      // etcd is the only component the API server both reads and writes.
      arrow(
        [ETCD.x + ETCD.w + 6, ETCD.y + ETCD.h / 2],
        [API_SERVER.x - 6, API_SERVER.y + 30],
        'neutral',
        { both: true },
      ),
      arrow(
        [CONTROLLER_MANAGER.x + CONTROLLER_MANAGER.w + 6, CONTROLLER_MANAGER.y + 22],
        [API_SERVER.x - 6, API_SERVER.y + 110],
        '5',
      ),
      arrow(
        [SCHEDULER.x + SCHEDULER.w + 6, SCHEDULER.y + 22],
        [API_SERVER.x - 6, API_SERVER.y + 168],
        '4',
      ),

      etcdCluster(),
      componentBox('kube-apiserver', API_SERVER, ['API', 'Server']),
      componentBox('kube-controller-manager', CONTROLLER_MANAGER, ['Controller Manager']),
      componentBox('kube-scheduler', SCHEDULER, ['Scheduler']),

      // --- workers ---
      planePill('worker', { x: 596, y: 14, w: 248, h: 46 }),
      workerNode(0),
      workerNode(1),
    ],
  );

  return el('figure', { className: ['arch-figure'], id: 'cluster-architecture' }, [
    el('div', { className: ['arch-scroll'] }, [svg]),
    el('figcaption', { className: ['arch-caption'] }, [txt(labels.caption)]),
  ]);
}
