import type { Timeseries } from "../types";

type Props = { series: Timeseries };

/** Dependency-free SVG line chart for copilot chart prompts. */
export function TrendChart({ series }: Props): JSX.Element {
  if (series.error || series.points.length === 0) {
    return <p className="error">{series.error ?? "no data"}</p>;
  }
  const W = 360;
  const H = 140;
  const PAD = 28;
  const ys = series.points.map((p) => p.y);
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);
  const span = yMax - yMin || 1;
  const x = (i: number): number =>
    PAD + (i * (W - 2 * PAD)) / Math.max(series.points.length - 1, 1);
  const y = (v: number): number => H - PAD - ((v - yMin) * (H - 2 * PAD)) / span;
  const path = series.points.map((p, i) => `${i === 0 ? "M" : "L"}${x(i)},${y(p.y)}`).join(" ");

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={series.metric}>
        <text x={PAD} y={14} fontSize="10" fill="#718096">
          {series.metric} ({series.unit ?? ""})
        </text>
        <path d={path} fill="none" stroke="#2b6cb0" strokeWidth="2" />
        {series.points.map((p, i) => (
          <g key={p.x}>
            <circle cx={x(i)} cy={y(p.y)} r="3" fill="#2b6cb0" />
            <text x={x(i)} y={H - 8} fontSize="8" fill="#a0aec0" textAnchor="middle">
              {p.x.slice(5)}
            </text>
            <text x={x(i)} y={y(p.y) - 6} fontSize="8" fill="#4a5568" textAnchor="middle">
              {p.y}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
