import { useState } from "react";
import { api } from "../api";
import type { GenerationResult } from "../types";
import { PlanView } from "./PlanView";
import { ProvenanceTrace } from "./ProvenanceTrace";

type Props = {
  result: GenerationResult | null;
  onResult: (r: GenerationResult) => void;
  defaultMinutes: number;
};

/** Generation state lives in App so the dashboard's session card can
 * mirror the latest KG-filtered plan. */
export function GeneratorPanel({ result, onResult, defaultMinutes }: Props): JSX.Element {
  const [prompt, setPrompt] = useState("");
  const [minutes, setMinutes] = useState(defaultMinutes);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      onResult(await api.generate(prompt, minutes));
    } catch (e) {
      setError(e instanceof Error ? e.message : "generation failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="view-grid">
      <div className="view-col">
        <div className="c c-pad rise">
          <div className="card-head">
            <span className="card-title">Workout generator</span>
          </div>
          <label className="field-lab" htmlFor="gen-prompt">
            Coach prompt
          </label>
          <textarea
            id="gen-prompt"
            className="input-area"
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder='e.g. "lower-body, her left knee is bothering her, exclude deadlifts"'
          />
          <div className="gen-controls">
            <span className="minutes-pill">
              minutes
              <input
                type="number"
                min={10}
                max={90}
                value={minutes}
                onChange={(e) => setMinutes(Number(e.target.value))}
              />
            </span>
            <button
              className="pill pill-accent pill-lg"
              disabled={busy || !prompt}
              onClick={() => void generate()}
            >
              {busy ? "Generating…" : "Generate plan"}
            </button>
          </div>
          {error && <p className="error-text">{error}</p>}
          {result?.error && <p className="error-text">{result.error}</p>}
        </div>
        {result && (
          <div className="c c-pad rise">
            <ProvenanceTrace provenance={result.provenance} events={result.trace.events} />
          </div>
        )}
      </div>
      <div className="view-col">
        {result?.plan ? (
          <div className="c c-pad rise">
            <div className="card-head">
              <span className="card-title">Plan</span>
              <span className="tag tag-accent">provenance attached</span>
            </div>
            <PlanView plan={result.plan} />
          </div>
        ) : (
          <div className="c c-pad rise center-note">
            Generated plans appear here — every one carries a provenance trace.
          </div>
        )}
      </div>
    </div>
  );
}
