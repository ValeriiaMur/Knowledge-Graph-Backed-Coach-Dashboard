import { useEffect, useState } from "react";
import { api } from "./api";
import type { MemberProfile } from "./types";
import { BriefCard } from "./components/BriefCard";
import { CopilotPanel } from "./components/CopilotPanel";
import { GeneratorPanel } from "./components/GeneratorPanel";
import { GraphView } from "./components/GraphView";
import { LoginGate } from "./components/LoginGate";
import { MemberHeader } from "./components/MemberHeader";

export function App(): JSX.Element {
  const [coach, setCoach] = useState<string | null>(null);
  const [member, setMember] = useState<MemberProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!coach) return;
    void api
      .member()
      .then(setMember)
      .catch(() => setError("Backend unreachable — run `make backend`."));
  }, [coach]);

  if (!coach) return <LoginGate onLogin={setCoach} />;
  if (error)
    return (
      <p className="error" style={{ padding: "2rem" }}>
        {error}
      </p>
    );
  if (!member)
    return (
      <p className="muted" style={{ padding: "2rem" }}>
        Loading member…
      </p>
    );

  return (
    <>
      <header className="app-header">
        <h1>Coach Dashboard</h1>
        <span>coach {coach}</span>
      </header>
      <MemberHeader member={member} />
      <div className="layout">
        <div>
          <BriefCard brief={member.coach_brief} />
          <div style={{ height: "1rem" }} />
          <GeneratorPanel />
        </div>
        <CopilotPanel />
        <GraphView />
      </div>
    </>
  );
}
