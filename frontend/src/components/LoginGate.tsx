import { useState } from "react";

type Props = { onLogin: (coach: string) => void };

/** Mock auth per spec — any name logs in. */
export function LoginGate({ onLogin }: Props): JSX.Element {
  const [name, setName] = useState("");
  return (
    <div className="login panel">
      <h2>Coach login</h2>
      <label className="field">
        Coach name
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && name && onLogin(name)}
          placeholder="e.g. Alex"
        />
      </label>
      <button className="btn" disabled={!name} onClick={() => onLogin(name)}>
        Open member view
      </button>
    </div>
  );
}
