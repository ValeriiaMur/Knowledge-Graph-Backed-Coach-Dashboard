import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { GraphData } from "../types";

const KIND_COLORS: Record<string, string> = {
  exercise: "#90cdf4",
  muscle: "#9ae6b4",
  joint: "#feb2b2",
  substructure: "#fbd38d",
  equipment: "#d6bcfa",
  movement_pattern: "#cbd5e0",
  condition: "#f687b3",
};

type Pos = { x: number; y: number };

/** KG 1 visualization: exercises on the outer ring, concepts on inner rings.
 * Click a node to highlight its edges. */
export function GraphView(): JSX.Element {
  const [data, setData] = useState<GraphData | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    void api
      .graph()
      .then(setData)
      .catch(() => setData(null));
  }, []);

  const layout = useMemo(() => {
    if (!data) return new Map<string, Pos>();
    const W = 900;
    const H = 560;
    const cx = W / 2;
    const cy = H / 2;
    const rings: Record<string, number> = {
      exercise: 260,
      movement_pattern: 195,
      equipment: 150,
      muscle: 105,
      joint: 60,
      substructure: 30,
      condition: 230,
    };
    const byKind = new Map<string, string[]>();
    for (const n of data.nodes) {
      byKind.set(n.kind, [...(byKind.get(n.kind) ?? []), n.id]);
    }
    const pos = new Map<string, Pos>();
    for (const [kind, ids] of byKind) {
      const r = rings[kind] ?? 220;
      ids.forEach((id, i) => {
        const angle = (2 * Math.PI * i) / ids.length - Math.PI / 2;
        pos.set(id, { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) });
      });
    }
    return pos;
  }, [data]);

  if (!data) return <div className="panel graph-panel muted">Loading graph…</div>;

  const visibleLinks = selected
    ? data.links.filter((l) => l.source === selected || l.target === selected)
    : [];

  return (
    <div className="panel graph-panel">
      <h2>
        Movement / clinical knowledge graph — {data.nodes.length} nodes, {data.links.length} edges
        {selected ? ` · ${selected}` : " · click a node"}
      </h2>
      <svg viewBox="0 0 900 560" width="100%">
        {visibleLinks.map((l, i) => {
          const a = layout.get(l.source);
          const b = layout.get(l.target);
          if (!a || !b) return null;
          return (
            <g key={`${l.source}-${l.target}-${i}`}>
              <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#2b6cb0" strokeWidth="1.2" />
              <text
                x={(a.x + b.x) / 2}
                y={(a.y + b.y) / 2}
                fontSize="7"
                fill="#2b6cb0"
                textAnchor="middle"
              >
                {l.rel}
              </text>
            </g>
          );
        })}
        {data.nodes.map((n) => {
          const p = layout.get(n.id);
          if (!p) return null;
          const active = selected === n.id;
          return (
            <circle
              key={n.id}
              cx={p.x}
              cy={p.y}
              r={active ? 7 : 4}
              fill={KIND_COLORS[n.kind] ?? "#cbd5e0"}
              stroke={active ? "#1a2c42" : "#fff"}
              strokeWidth="1"
              style={{ cursor: "pointer" }}
              onClick={() => setSelected(active ? null : n.id)}
            >
              <title>
                {n.kind}: {n.name}
              </title>
            </circle>
          );
        })}
      </svg>
      <div className="quick-row">
        {Object.entries(KIND_COLORS).map(([kind, color]) => (
          <span key={kind} className="badge" style={{ background: color }}>
            {kind}
          </span>
        ))}
      </div>
    </div>
  );
}
