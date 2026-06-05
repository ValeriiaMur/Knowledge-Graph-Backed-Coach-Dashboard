import { iconForExercise } from "../derive";
import { iconByName } from "../icons";
import type { PlanItem, WorkoutPlan } from "../types";

type Props = { plan: WorkoutPlan };

function Item({ item }: { item: PlanItem }): JSX.Element {
  const Ic = iconByName(iconForExercise(item.name));
  const dose = item.reps ? `${item.sets}×${item.reps}` : `${item.sets}×${item.duration_sec ?? 30}s`;
  return (
    <div className="gear-item">
      <span className="gear-ic">
        <Ic size={20} />
      </span>
      <div style={{ minWidth: 0 }}>
        <div className="nm">{item.name}</div>
        <div className="sub">rest {item.rest_sec}s</div>
      </div>
      <span className="plan-dose">{dose}</span>
    </div>
  );
}

export function PlanView({ plan }: Props): JSX.Element {
  const sections: [string, PlanItem[]][] = [
    ["Warmup", plan.warmup],
    ["Main", plan.main],
    ["Cooldown", plan.cooldown],
  ];
  return (
    <div>
      {sections.map(([title, items]) => (
        <div key={title} className="plan-sec">
          <span className="eyebrow">{title}</span>
          {items.map((item) => (
            <Item key={`${title}-${item.exercise}`} item={item} />
          ))}
        </div>
      ))}
    </div>
  );
}
