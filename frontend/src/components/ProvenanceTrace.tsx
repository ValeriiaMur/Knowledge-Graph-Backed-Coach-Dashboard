import type { Provenance, TraceEvent } from "../types";

type Props = { provenance: Provenance; events: TraceEvent[] };

/** Why the plan looks the way it does — resolved concepts, what safety
 * filtered (with the graph path), substitutes, and pipeline timings. */
export function ProvenanceTrace({ provenance, events }: Props): JSX.Element {
  return (
    <div className="prov-block">
      <details open>
        <summary>
          Provenance — {provenance.allowed_count} allowed · {provenance.removed.length} filtered
        </summary>

        {provenance.resolved_concepts.map((c) => (
          <div key={c.query} className="prov-row">
            “{c.query}” → <strong>{c.node_id}</strong>
            <span className="mono">
              {c.method} · confidence {c.confidence}
            </span>
          </div>
        ))}
        {provenance.unresolved.map((u) => (
          <div key={u} className="prov-row warn">
            Couldn’t map “{u}” — please clarify; it was NOT silently dropped.
          </div>
        ))}
        {provenance.down_ranked.length > 0 && (
          <div className="prov-row warn">
            Down-ranked (condition caution): {provenance.down_ranked.join(", ")}
          </div>
        )}

        {provenance.removed.map((r) => (
          <div key={r.node_id} className="prov-row removed">
            <strong>{r.name}</strong> — {r.reason}
            <span className="mono">{r.graph_path}</span>
            {r.substitutes.length > 0 && (
              <span className="muted-text">substitutes: {r.substitutes.join(", ")}</span>
            )}
          </div>
        ))}
      </details>
      {provenance.selected.length > 0 && (
        <details>
          <summary>Why each exercise was chosen — {provenance.selected.length}</summary>
          {provenance.selected.map((s) => (
            <div key={s.node_id} className="prov-row">
              <strong>{s.name}</strong> — {s.reason}
              <span className="mono">{s.graph_path}</span>
            </div>
          ))}
        </details>
      )}
      <details>
        <summary>Pipeline trace</summary>
        {events.map((e) => (
          <div key={e.step} className="muted-text">
            {e.step}: {e.ms}ms
          </div>
        ))}
      </details>
    </div>
  );
}
