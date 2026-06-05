import type { MemberProfile } from "../types";

type Props = { brief: MemberProfile["coach_brief"] };

export function BriefCard({ brief }: Props): JSX.Element {
  return (
    <div className="panel">
      <h2>Morning brief — {brief.generated_for}</h2>
      {brief.morning_tasks.map((t) => (
        <div key={t.text} className="brief-task">
          <strong>{t.type}</strong>: {t.text}
        </div>
      ))}
      <p className="muted">
        Churn risk <strong>{brief.churn_risk.level}</strong>: {brief.churn_risk.reasons.join("; ")}
      </p>
    </div>
  );
}
