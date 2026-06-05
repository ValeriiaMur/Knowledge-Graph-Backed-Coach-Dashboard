import { dayBadge, initials } from "../derive";
import type { MemberProfile } from "../types";

type Props = { member: MemberProfile; now: Date };

export function ProfileCard({ member, now }: Props): JSX.Element {
  const { profile } = member;
  return (
    <div className="c c-pad g-profile rise" style={{ animationDelay: ".05s" }}>
      <div className="profile-photo">
        {/* dataset is synthetic — no member photo, so an initials avatar fills the slot */}
        <div className="avatar-fill">
          <span className="avatar-initials">{initials(profile.name)}</span>
        </div>
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
