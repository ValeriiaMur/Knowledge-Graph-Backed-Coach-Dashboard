import { useState } from "react";
import { api } from "../api";
import type { GenerationResult } from "../types";
import { PlanView } from "./PlanView";
import { ProvenanceTrace } from "./ProvenanceTrace";

export function GeneratorPanel(): JSX.Element {
  const [prompt, setPrompt] = useState("");
  const [minutes, setMinutes] = useState(30);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generate = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      setResult(await api.generate(prompt, minutes));
    } catch (e) {
      setError(e instanceof Error ? e.message : "generation failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="panel">
      <h2>Workout generator</h2>
      <label className="field">
        Coach prompt
        <textarea
          rows={2}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder='e.g. "lower-body, her left knee is bothering her, exclude deadlifts"'
        />
      </label>
      <label className="field">
        Time window (minutes)
        <input
          type="number"
          min={10}
          max={90}
          value={minutes}
          onChange={(e) => setMinutes(Number(e.target.value))}
        />
      </label>
      <button className="btn" disabled={busy || !prompt} onClick={() => void generate()}>
        {busy ? "Generating…" : "Generate plan"}
      </button>

      {error && <p className="error">{error}</p>}
      {result?.error && <p className="error">{result.error}</p>}
      {result?.plan && <PlanView plan={result.plan} />}
      {result && <ProvenanceTrace provenance={result.provenance} events={result.trace.events} />}
    </div>
  );
}
