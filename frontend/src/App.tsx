import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { GenerationResult, MemberProfile } from "./types";
import { AccordionCard } from "./components/AccordionCard";
import { BriefCard } from "./components/BriefCard";
import { CalendarCard } from "./components/CalendarCard";
import { CopilotPanel } from "./components/CopilotPanel";
import { GeneratorPanel } from "./components/GeneratorPanel";
import { GraphView } from "./components/GraphView";
import { Hero } from "./components/Hero";
import { LoginGate } from "./components/LoginGate";
import { ProfileCard } from "./components/ProfileCard";
import { ProgramCard } from "./components/ProgramCard";
import { ProgressCard } from "./components/ProgressCard";
import { SessionCard } from "./components/SessionCard";
import { TimerCard } from "./components/TimerCard";
import { TopNav, type NavTab } from "./components/TopNav";

export function App(): JSX.Element {
  const [coach, setCoach] = useState<string | null>(null);
  const [member, setMember] = useState<MemberProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<NavTab>("Dashboard");
  const [generation, setGeneration] = useState<GenerationResult | null>(null);
  const now = useMemo(() => new Date(), []);

  useEffect(() => {
    if (!coach) return;
    void api
      .member()
      .then(setMember)
      .catch(() => setError("Backend unreachable — run `make backend`."));
  }, [coach]);

  if (!coach) return <LoginGate onLogin={setCoach} />;

  return (
    <div className="stage">
      <div className="panel">
        <TopNav active={tab} onSelect={setTab} coach={coach} />
        {error && <p className="error-text">{error}</p>}
        {!member && !error && <p className="center-note">Loading member…</p>}
        {member && tab === "Dashboard" && (
          <>
            <Hero member={member} />
            <div className="grid">
              <ProfileCard member={member} now={now} />
              <AccordionCard member={member} />
              <ProgressCard history={member.workout_history} now={now} />
              <TimerCard targetMinutes={member.preferences.preferred_session_minutes} />
              <CalendarCard member={member} now={now} />
              <div className="g-right">
                <BriefCard brief={member.coach_brief} />
                <ProgramCard member={member} />
                <SessionCard
                  member={member}
                  generation={generation}
                  onGoGenerate={() => setTab("Generate")}
                />
              </div>
            </div>
          </>
        )}
        {member && tab === "Generate" && (
          <GeneratorPanel
            result={generation}
            onResult={setGeneration}
            defaultMinutes={member.preferences.preferred_session_minutes}
          />
        )}
        {member && tab === "Coach" && (
          <div className="view-grid">
            <CopilotPanel />
            <BriefCard brief={member.coach_brief} />
          </div>
        )}
        {member && tab === "Graph" && <GraphView />}
      </div>
    </div>
  );
}
