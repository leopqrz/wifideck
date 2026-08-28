import type { Config } from "tailwindcss";

// WiFiDeck design tokens — the locked "command-center" identity.
// Mirrors docs/roadmap.html and the design-system note. Keep these exact.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#080b0f",
        "bg-grid": "#0c1218",
        panel: "#10161d",
        "panel-2": "#141d26",
        line: "#223140",
        "line-soft": "#1a2530",
        text: "#dbe4ec",
        head: "#eef4f9",
        muted: "#7b8a99",
        faint: "#55636f",
        accent: "#2fd6d6",
        "accent-dim": "#1c8a8a",
        ok: "#3ad07f",
        warn: "#f2a93b",
        crit: "#f0555b",
      },
      fontFamily: {
        display: ['"Chakra Petch"', '"IBM Plex Sans"', "system-ui", "sans-serif"],
        body: ['"IBM Plex Sans"', "system-ui", "-apple-system", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      letterSpacing: {
        hud: "0.18em",
      },
    },
  },
  plugins: [],
} satisfies Config;
