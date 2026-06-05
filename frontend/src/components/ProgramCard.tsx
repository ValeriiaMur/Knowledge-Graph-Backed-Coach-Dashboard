import { buildProgram } from "../derive";
import type { MemberProfile } from "../types";

type Props = { member: MemberProfile };

export function ProgramCard({ member }: Props): JSX.Element {
  const program = buildProgram(member);
  return (
    <div className="c c-pad rise" style={{ animationDelay: ".14s" }}>
      <div className="card-head" style={{ marginBottom: 18 }}>
        <span className="card-title">{program.title}</span>
        <span style={{ fontSize: 30, fontWeight: 700, letterSpacing: "-1px" }}>{program.pct}</span>
      </div>
      <div className="prog-segs">
        {program.segs.map((s) => (
          <div key={s.lab} className="prog-seg" style={{ flex: s.flex }}>
            <span className="pc">{s.val}</span>
            <div className={"prog-bar seg-" + s.style}>{s.lab}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
