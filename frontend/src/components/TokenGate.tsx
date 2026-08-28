import { useState } from "react";
import { setToken } from "../api/client";

// Shown when the backend rejects the current token (401). The user pastes the
// token the installer printed; it's saved to localStorage and the app reloads.
export function TokenGate() {
  const [value, setValue] = useState("");

  function save() {
    if (!value.trim()) return;
    setToken(value.trim());
    location.reload();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg/90 backdrop-blur">
      <div className="w-[min(420px,90vw)] rounded-[10px] border border-line bg-panel p-6">
        <div className="font-display text-lg font-bold uppercase tracking-[0.10em] text-head">
          WIFI<span className="text-accent">DECK</span>
        </div>
        <p className="mt-3 text-sm text-muted">
          Enter your access token. It's in{" "}
          <span className="font-mono text-text">/opt/wifideck/backend/.env</span>{" "}
          (<span className="font-mono text-text">WIFIDECK_TOKEN</span>), printed by the installer.
        </p>
        <input
          type="password"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && save()}
          placeholder="paste token"
          autoFocus
          className="mt-4 w-full rounded border border-line bg-panel-2 px-3 py-2 font-mono text-sm text-text outline-none focus:border-accent"
        />
        <button
          onClick={save}
          disabled={!value.trim()}
          className="mt-3 w-full rounded bg-accent px-4 py-2 font-display text-sm font-semibold text-bg disabled:opacity-40"
        >
          Connect
        </button>
      </div>
    </div>
  );
}
