import type { MemberProfile } from "../types";

type Props = { member: MemberProfile };

export function MemberHeader({ member }: Props): JSX.Element {
  const { profile, injuries, equipment_available, coach_brief } = member;
  return (
    <div className="member-bar">
      <strong>
        {profile.name} · {profile.age} · {profile.sex}
      </strong>
      {injuries.map((inj) => (
        <span key={inj.region} className="badge badge-injury">
          {inj.region} — {inj.status} ({inj.severity})
        </span>
      ))}
      <span className="badge badge-risk">churn risk: {coach_brief.churn_risk.level}</span>
      <span className="badge badge-equip">equipment: {equipment_available.join(", ")}</span>
    </div>
  );
}
