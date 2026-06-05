import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles/future-ds.css";
import "./styles/dashboard.css";
import "./styles/app.css";

const rootEl = document.getElementById("root");
if (!rootEl) throw new Error("Missing #root element");

createRoot(rootEl).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

/* Enable entrance animations only when the page is actually visible, so cards
   never sit frozen at opacity:0 in a backgrounded/capture context. */
function enableEntrance(): void {
  const go = (): void => {
    if (document.visibilityState === "visible") {
      requestAnimationFrame(() => document.documentElement.classList.add("anim-in"));
      document.removeEventListener("visibilitychange", go);
    }
  };
  if (document.visibilityState === "visible") go();
  else document.addEventListener("visibilitychange", go);
}
enableEntrance();
