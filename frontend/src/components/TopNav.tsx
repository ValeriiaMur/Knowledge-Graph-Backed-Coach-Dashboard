import { Icons } from "../icons";

export type NavTab = "Dashboard" | "Generate" | "Coach" | "Graph";

export const NAV_TABS: NavTab[] = ["Dashboard", "Generate", "Coach", "Graph"];

type Props = {
  active: NavTab;
  onSelect: (tab: NavTab) => void;
  coach: string;
  onDemo: (context: string) => void;
};

export function TopNav({ active, onSelect, coach, onDemo }: Props): JSX.Element {
  return (
    <div className="nav">
      <div className="brand">
        <span className="mark"></span> Future Coach
      </div>
      <div className="navtabs">
        {NAV_TABS.map((t) => (
          <button
            key={t}
            className={"navtab" + (active === t ? " active" : "")}
            onClick={() => onSelect(t)}
          >
            {t}
          </button>
        ))}
      </div>
      <div className="navright">
        <button className="setting" onClick={() => onDemo("Settings")}>
          <Icons.gear size={17} /> {coach}
        </button>
        <button
          className="iconbtn dotbell"
          aria-label="Notifications"
          onClick={() => onDemo("Notifications")}
        >
          <Icons.bell size={19} />
        </button>
        <button
          className="iconbtn iconbtn-dark"
          aria-label="Profile"
          onClick={() => onDemo("Profile")}
        >
          <Icons.user size={19} />
        </button>
      </div>
    </div>
  );
}
