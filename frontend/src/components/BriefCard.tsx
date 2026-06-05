import { Icons, iconByName } from "../icons";
import type { MemberProfile } from "../types";

type Props = { brief: MemberProfile["coach_brief"] };

const TASK_ICONS: Record<string, keyof typeof Icons> = {
  celebrate: "flame",
  review_risk: "bell",
};

export function BriefCard({ brief }: Props): JSX.Element {
  return (
    <div className="c c-pad rise" style={{ animationDelay: ".12s" }}>
      <div className="card-head" style={{ marginBottom: 8 }}>
        <span className="card-title">Morning brief</span>
        <span className="tag">{brief.generated_for}</span>
      </div>
      {brief.morning_tasks.map((t) => {
        const Ic = iconByName(TASK_ICONS[t.type] ?? "bell");
        return (
          <div key={t.text} className="brief-item">
            <span className="gear-ic">
              <Ic size={18} />
            </span>
            <div className="txt">{t.text}</div>
          </div>
        );
      })}
      <div className="brief-risk">
        <span className={brief.churn_risk.level === "low" ? "tag" : "tag tag-accent"}>
          churn risk · {brief.churn_risk.level}
        </span>
        <div className="reasons">{brief.churn_risk.reasons.join(" · ")}</div>
      </div>
    </div>
  );
}
