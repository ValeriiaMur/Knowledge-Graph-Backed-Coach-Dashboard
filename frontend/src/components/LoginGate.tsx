import { useState } from "react";

type Props = { onLogin: (coach: string) => void };

/** Mock auth per spec — any name logs in. Styled with Future DS primitives. */
export function LoginGate({ onLogin }: Props): JSX.Element {
  const [name, setName] = useState("");
  return (
    <div className="login-stage">
      <div className="card login-card rise">
        <div className="brand">
          <span className="mark"></span> Future Coach
        </div>
        <div className="hello">Welcome back</div>
        <label className="field-lab" htmlFor="coach-name">
          Coach name
        </label>
        <input
          id="coach-name"
          className="input-pill"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && name && onLogin(name)}
          placeholder="e.g. Alex"
        />
        <div style={{ marginTop: 16 }}>
          <button
            className="pill pill-accent pill-lg"
            disabled={!name}
            onClick={() => onLogin(name)}
          >
            Open member view
          </button>
        </div>
      </div>
    </div>
  );
}
