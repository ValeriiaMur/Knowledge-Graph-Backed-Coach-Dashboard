import { dayBadge } from "../derive";
import type { MemberProfile } from "../types";
import portrait from "../assets/jordan-rivera.svg";

type Props = { member: MemberProfile; now: Date };

export function ProfileCard({ member, now }: Props): JSX.Element {
  const { profile } = member;
  return (
    <div className="c c-pad g-profile rise" style={{ animationDelay: ".05s" }}>
      <div className="profile-photo">
        {/* synthetic illustrated portrait — fictional member, generated for the
            demo per the spec's synthetic-data rule (no real person) */}
        <img className="profile-img" src={portrait} alt={`${profile.name} (illustration)`} />
        <div className="profile-grad"></div>
        <div className="profile-meta">
          <div>
            <div className="nm">{profile.name}</div>
            <div className="role">
              {profile.tier ?? "Member"} · {profile.age} · {profile.sex}
            </div>
          </div>
          <div className="badge-pill">{dayBadge(profile.member_since, now)}</div>
        </div>
      </div>
    </div>
  );
}
