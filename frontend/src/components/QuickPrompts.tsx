type Props = { prompts: string[]; onPick: (p: string) => void; disabled: boolean };

export function QuickPrompts({ prompts, onPick, disabled }: Props): JSX.Element {
  return (
    <div className="quick-row">
      {prompts.map((p) => (
        <button key={p} className="pill pill-outline" disabled={disabled} onClick={() => onPick(p)}>
          {p}
        </button>
      ))}
    </div>
  );
}
