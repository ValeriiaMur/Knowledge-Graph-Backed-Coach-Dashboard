import { buildKpis, buildStatbar, firstName } from "../derive";
import { iconByName } from "../icons";
import type { MemberProfile } from "../types";
import { Fragment } from "react";

type Props = { member: MemberProfile };

export function Hero({ member }: Props): JSX.Element {
  const statbar = buildStatbar(member);
  const kpis = buildKpis(member);
  return (
    <div className="hero">
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="hello">
          Member focus: <span className="accentword">{firstName(member.profile.name)}</span>
        </div>
        <div className="statbar">
          {statbar.map((s) => (
            <div key={s.lab} className={"stat-item" + (s.grow ? " grow" : "")}>
              <div className="stat-lab">{s.lab}</div>
              <div className={"seg seg-" + s.style} style={s.grow ? undefined : { minWidth: 92 }}>
                {s.val}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="kpis">
        {kpis.map((k, i) => {
          const Ic = iconByName(k.icon);
          return (
            <Fragment key={k.label}>
              {i > 0 ? <div className="kpi-divide" /> : null}
              <div className="kpi">
                <div className="kpi-h">
                  <span className="i">
                    <Ic size={16} />
                  </span>
                  {k.label}
                </div>
                <div className="kpi-n">
                  {k.n}
                  {k.suffix ? <small>{k.suffix}</small> : null}
                </div>
              </div>
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}
