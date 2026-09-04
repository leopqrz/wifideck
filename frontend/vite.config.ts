/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies API + WebSocket to the backend so the browser talks to a
// single origin (no CORS friction) during development. The backend port is
// configurable (WIFIDECK_BACKEND_PORT) so you can dodge a busy 8787 — e.g. when
// VS Code is already forwarding it from a VM.
const backendPort = process.env.WIFIDECK_BACKEND_PORT || "8787";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": { target: `http://127.0.0.1:${backendPort}`, changeOrigin: true },
      "/ws": { target: `ws://127.0.0.1:${backendPort}`, ws: true },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: true,
  },
});
