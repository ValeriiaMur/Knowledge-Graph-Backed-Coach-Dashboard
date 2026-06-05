import type { GraphData, GraphNode } from "../types";

type Props = {
  node: GraphNode;
  data: GraphData;
  /** node position as a fraction of the svg viewBox (0..1) */
  x: number;
  y: number;
  onClose: () => void;
  onJump: (id: string) => void;
};

const REL_LABELS: Record<string, string> = {
  targets: "Targets",
  stresses: "Stresses",
  requires: "Requires",
  follows: "Pattern",
  part_of: "Part of",
  located_in: "Located in",
  contraindicated_for: "Contraindicated",
};

type Neighbor = { node: GraphNode; rel: string; mode?: string; out: boolean };

function neighborsOf(id: string, data: GraphData): Neighbor[] {
  const byId = new Map(data.nodes.map((n) => [n.id, n]));
  const result: Neighbor[] = [];
  for (const link of data.links) {
    const other = link.source === id ? link.target : link.target === id ? link.source : null;
    if (!other) continue;
    const node = byId.get(other);
    if (node) {
      const neighbor: Neighbor = { node, rel: link.rel, out: link.source === id };
      if (link.mode !== undefined) neighbor.mode = link.mode;
      result.push(neighbor);
    }
  }
  return result;
}

/** Floating detail card for a clicked KG node — everything the graph knows:
 * SNOMED mappings, exercise attributes, and grouped relations. */
export function GraphNodePopover({ node, data, x, y, onClose, onJump }: Props): JSX.Element {
  const neighbors = neighborsOf(node.id, data);
  const grouped = new Map<string, Neighbor[]>();
  for (const n of neighbors) {
    const key = n.out ? n.rel : `${n.rel}:in`;
    grouped.set(key, [...(grouped.get(key) ?? []), n]);
  }

  const style: React.CSSProperties = {
    left: `${Math.min(Math.max(x * 100, 4), 64)}%`,
    top: `${Math.min(Math.max(y * 100, 4), 55)}%`,
  };

  return (
    <div className="c node-pop rise" style={style}>
      <div className="node-pop-head">
        <div>
          <div className="nm">{node.name}</div>
          <span className="tag tag-ink">{node.kind.replace("_", " ")}</span>
        </div>
        <button className="expand" aria-label="Close" onClick={onClose}>
          ×
        </button>
      </div>

      {(node.priority_tier !== undefined || node.is_bilateral !== undefined) && (
        <div className="node-pop-row">
          {node.priority_tier !== undefined && (
            <span className="tag">tier {node.priority_tier}</span>
          )}
          {node.is_bilateral !== undefined && (
            <span className="tag">{node.is_bilateral ? "bilateral" : "unilateral"}</span>
          )}
          {node.side && <span className="tag">{node.side}</span>}
        </div>
      )}

      {node.skos_mappings && node.skos_mappings.length > 0 && (
        <div className="node-pop-sec">
          <span className="eyebrow">Ontology mappings</span>
          {node.skos_mappings.map((m) => (
            <div key={`${m.scheme}-${m.label}`} className="node-pop-map">
              <span className="tag tag-accent">
                {m.scheme}
                {m.code ? ` · ${m.code}` : ""}
              </span>
              <span className="lbl">
                {m.label} · {m.match.replace("skos:", "")}
                {m.verified ? " ✓" : " (unverified)"}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="node-pop-sec node-pop-scroll no-sb">
        {[...grouped.entries()].map(([key, items]) => {
          const rel = key.endsWith(":in") ? key.slice(0, -3) : key;
          const incoming = key.endsWith(":in");
          const label = incoming
            ? `${REL_LABELS[rel] ?? rel} ← (${items.length})`
            : `${REL_LABELS[rel] ?? rel} (${items.length})`;
          return (
            <div key={key}>
              <span className="eyebrow">{label}</span>
              <div className="node-pop-chips">
                {items.map((n) => (
                  <button
                    key={`${key}-${n.node.id}`}
                    className={"pill pill-outline" + (n.mode === "exclude" ? " pill-dark" : "")}
                    onClick={() => onJump(n.node.id)}
                    title={n.mode ? `mode: ${n.mode}` : n.node.id}
                  >
                    {n.node.name}
                    {n.mode ? ` · ${n.mode === "down_rank" ? "down-rank" : n.mode}` : ""}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
