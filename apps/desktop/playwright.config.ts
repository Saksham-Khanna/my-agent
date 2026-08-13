import { defineConfig, devices } from "@playwright/test";

const BACKEND_PORT = 8000;
const FRONTEND_PORT = 4173;

/**
 * End-to-end tests run against the REAL backend (FastAPI + WebSocket on
 * port 8000) and a production build of the desktop UI served by `vite
 * preview`. Both are started automatically by Playwright's webServer; set
 * `reuseExistingServer` so a locally-running backend is not duplicated.
 *
 * Local quickstart:
 *   npm run build            # one-time, so `vite preview` has an artifact
 *   npm run test:e2e         # starts backend + preview, runs e2e/*
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: `http://127.0.0.1:${FRONTEND_PORT}`,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `uvicorn app.main:app --port ${BACKEND_PORT}`,
      cwd: "../api",
      url: `http://127.0.0.1:${BACKEND_PORT}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
    {
      command: `npm run preview -- --port ${FRONTEND_PORT} --host 127.0.0.1`,
      url: `http://127.0.0.1:${FRONTEND_PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
  ],
});
