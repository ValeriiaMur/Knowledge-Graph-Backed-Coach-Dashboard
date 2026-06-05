import { useEffect, useState } from "react";
import { buildSession } from "../derive";
import { Icons, iconByName } from "../icons";
import type { GenerationResult, MemberProfile } from "../types";

type Props = {
  member: MemberProfile;
  generation: GenerationResult | null;
  onGoGenerate: () => void;
};

/** Dark checklist: shows the KG-filtered generated plan when one exists,
 * otherwise the member's latest real session from workout history. */
export function SessionCard({ member, generation, onGoGenerate }: Props): JSX.Element {
  const session = buildSession(generation, member);
  const [done, setDone] = useState<boolean[]>(() =>
    session ? session.items.map((x) => x.done) : [],
  );

  const sessionKey = session ? session.title + session.items.length : "";
  useEffect(() => {
    setDone(session ? session.items.map((x) => x.done) : []);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- re-seed only when the session itself changes
  }, [sessionKey]);

  if (!session) {
    return (
      <div className="darkcard rise" style={{ animationDelay: ".18s" }}>
        <div className="dh">
          <span className="t">Today&apos;s session</span>
        </div>
        <div className="empty-session">
          <span>No plan yet for this member.</span>
          <button className="pill pill-accent" onClick={onGoGenerate}>
            Generate a session
          </button>
        </div>
      </div>
    );
  }

  const count = done.filter(Boolean).length;
  return (
    <div className="darkcard rise" style={{ animationDelay: ".18s" }}>
      <div className="dh">
        <span className="t">{session.title}</span>
        <span className="c">
          {count}/{session.items.length}
        </span>
      </div>
      {session.items.map((it, i) => {
        const G = iconByName(it.ic);
        return (
          <div key={`${it.nm}-${i}`} className={"task" + (done[i] ? " done" : "")}>
            <span className="task-ic">
              <G size={19} />
            </span>
            <div style={{ minWidth: 0 }}>
              <div className="nm">{it.nm}</div>
              <div className="sub">{it.sub}</div>
            </div>
            <span
              className={"check" + (done[i] ? " on" : "")}
              onClick={() => setDone((d) => d.map((v, k) => (k === i ? !v : v)))}
            >
              <Icons.check size={15} />
            </span>
          </div>
        );
      })}
    </div>
  );
}
