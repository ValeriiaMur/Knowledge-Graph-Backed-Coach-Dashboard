import type { PlanItem, WorkoutPlan } from "../types";

type Props = { plan: WorkoutPlan };

function Item({ item }: { item: PlanItem }): JSX.Element {
  const dose = item.reps ? `${item.sets}×${item.reps}` : `${item.sets}×${item.duration_sec ?? 30}s`;
  return (
    <div className="plan-item">
      <span>{item.name}</span>
      <span>
        {dose} · rest {item.rest_sec}s
      </span>
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
        <div key={title} className="plan-section">
          <h3>{title}</h3>
          {items.map((item) => (
            <Item key={`${title}-${item.exercise}`} item={item} />
          ))}
        </div>
      ))}
    </div>
  );
}
