import { useEffect, useState } from "react";

type Health = { status: string };

export function App(): JSX.Element {
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    void fetch("/api/health")
      .then((r) => r.json() as Promise<Health>)
      .then(setHealth)
      .catch(() => setHealth({ status: "backend unreachable" }));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui", padding: "2rem" }}>
      <h1>Coach Dashboard</h1>
      <p>Phase 1 shell — backend: {health?.status ?? "checking…"}</p>
    </main>
  );
}
