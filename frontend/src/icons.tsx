/* Future Coach — inline icon set from the design handoff (stroke = currentColor).
 * Kept as a single module mirroring dash-icons.jsx 1:1; these are SVG glyphs,
 * not page components, so the one-component-per-file rule doesn't apply. */

export type IconProps = { size?: number; sw?: number };
export type IconComponent = (p?: IconProps) => JSX.Element;

const svgProps = (
  p: IconProps,
): {
  width: number;
  height: number;
  viewBox: string;
  fill: string;
  stroke: string;
  strokeWidth: number;
  strokeLinecap: "round";
  strokeLinejoin: "round";
} => ({
  width: p.size ?? 18,
  height: p.size ?? 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: p.sw ?? 1.7,
  strokeLinecap: "round",
  strokeLinejoin: "round",
});

export const Icons = {
  dumbbell: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="M6.5 7v10M3.5 9v6M17.5 7v10M20.5 9v6M6.5 12h11" />
    </svg>
  ),
  flame: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="M12 3c1.5 3 4 4 4 7a4 4 0 0 1-8 0c0-1.2.4-2 1-2.8C9.4 7 11 6 12 3Z" />
      <path d="M12 21a5 5 0 0 0 5-5c0-2-1-3.2-2-4.5" />
    </svg>
  ),
  bolt: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="M13 3 5 13h6l-1 8 8-10h-6l1-8Z" />
    </svg>
  ),
  gear: (p = {}) => (
    <svg {...svgProps(p)}>
      <circle cx="12" cy="12" r="3.2" />
      <path d="M12 3v2.5M12 18.5V21M21 12h-2.5M5.5 12H3M18 6l-1.8 1.8M7.8 16.2 6 18M18 18l-1.8-1.8M7.8 7.8 6 6" />
    </svg>
  ),
  bell: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z" />
      <path d="M10 19a2 2 0 0 0 4 0" />
    </svg>
  ),
  user: (p = {}) => (
    <svg {...svgProps(p)}>
      <circle cx="12" cy="8.5" r="3.5" />
      <path d="M5.5 19a6.5 6.5 0 0 1 13 0" />
    </svg>
  ),
  arrowUR: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="M7 17 17 7M9 7h8v8" />
    </svg>
  ),
  play: (p = {}) => (
    <svg {...svgProps({ ...p, sw: p.sw ?? 1.4 })}>
      <path d="M8 5.5v13l11-6.5-11-6.5Z" fill="currentColor" />
    </svg>
  ),
  pause: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="M9 5v14M15 5v14" />
    </svg>
  ),
  reset: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="M4 12a8 8 0 1 1 2.3 5.6M4 12V7M4 12h5" />
    </svg>
  ),
  clock: (p = {}) => (
    <svg {...svgProps(p)}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 1.8" />
    </svg>
  ),
  chevron: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="m6 9 6 6 6-6" />
    </svg>
  ),
  dots: (p = {}) => (
    <svg {...svgProps(p)}>
      <circle cx="5" cy="12" r="1.4" fill="currentColor" />
      <circle cx="12" cy="12" r="1.4" fill="currentColor" />
      <circle cx="19" cy="12" r="1.4" fill="currentColor" />
    </svg>
  ),
  check: (p = {}) => (
    <svg {...svgProps({ ...p, sw: p.sw ?? 2.2 })}>
      <path d="m5 12.5 4.5 4.5L19 7" />
    </svg>
  ),
  barbell: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="M3 10v4M6 8v8M18 8v8M21 10v4M6 12h12" />
    </svg>
  ),
  row: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="M4 12h10M14 9l3 3-3 3M18 7v10" />
    </svg>
  ),
  band: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="M5 8c4 3 10 3 14 0M5 16c4-3 10-3 14 0" />
    </svg>
  ),
  squat: (p = {}) => (
    <svg {...svgProps(p)}>
      <circle cx="12" cy="5.5" r="1.8" />
      <path d="M12 8v4l-3 4M12 12l3 4M7 9h10" />
    </svg>
  ),
  dead: (p = {}) => (
    <svg {...svgProps(p)}>
      <circle cx="12" cy="5.5" r="1.8" />
      <path d="M12 8v6M9 14l3-2 3 2M8 18h8" />
    </svg>
  ),
  lunge: (p = {}) => (
    <svg {...svgProps(p)}>
      <circle cx="13" cy="5.5" r="1.8" />
      <path d="M13 8l-2 3 4 2M11 11l-4 5M15 13l1 4" />
    </svg>
  ),
  core: (p = {}) => (
    <svg {...svgProps(p)}>
      <path d="M5 18h14M12 6v8M9 9l3-3 3 3" />
    </svg>
  ),
  plank: (p = {}) => (
    <svg {...svgProps(p)}>
      <circle cx="6" cy="9" r="1.6" />
      <path d="M7.5 10 18 14M5 18l4-6M18 14v4" />
    </svg>
  ),
  stretch: (p = {}) => (
    <svg {...svgProps(p)}>
      <circle cx="9" cy="5.5" r="1.8" />
      <path d="M9 8v5l5 3M9 13l-3 4" />
    </svg>
  ),
} satisfies Record<string, IconComponent>;

const ICONS_BY_NAME: Record<string, IconComponent> = Icons;

export function iconByName(name: string): IconComponent {
  return ICONS_BY_NAME[name] ?? Icons.dumbbell;
}
