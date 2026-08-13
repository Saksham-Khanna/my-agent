import { test, expect, type Page } from "@playwright/test";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

/**
 * Opens the desktop shell and waits until it reports a live WebSocket
 * connection to the real backend.
 */
async function openConnectedApp(page: Page): Promise<void> {
  await page.goto("/");
  await expect(page.getByTestId("backend-status")).toHaveText(/Backend: Connected/, {
    timeout: 20000,
  });
}

test.describe("Spectra shell against the real backend", () => {
  test("backend health endpoint reports ok", async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/health`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.status).toBe("ok");
  });

  test("app connects to the backend WebSocket", async ({ page }) => {
    await openConnectedApp(page);
    await expect(page.getByTestId("backend-status")).toHaveText("Backend: Connected");
  });

  test("orb starts in IDLE once connected", async ({ page }) => {
    await openConnectedApp(page);
    await expect(page.locator("[data-orb-state]")).toHaveAttribute("data-orb-state", "IDLE");
  });

  test("mode dock lets the user switch modes", async ({ page }) => {
    await openConnectedApp(page);
    const actions = page.getByRole("tab", { name: "Actions" });
    await actions.click();
    await expect(actions).toHaveAttribute("aria-selected", "true");
    await expect(actions).toHaveAttribute("tabindex", "0");
  });

  test("an actions command runs a real tool end-to-end", async ({ page }) => {
    await openConnectedApp(page);

    await page.getByRole("tab", { name: "Actions" }).click();
    await page.getByLabel("Command input").fill("sysinfo");
    await page.getByLabel("Send").click();

    // The tool output streams back over the WebSocket into the UI.
    await expect(page.locator(".response-panel")).toContainText(
      "[Executed Tool 'system_info']",
      { timeout: 20000 },
    );

    // The task cycle completes and the orb returns to IDLE.
    await expect(page.locator("[data-orb-state]")).toHaveAttribute("data-orb-state", "IDLE", {
      timeout: 20000,
    });
  });

  test("a memory command persists to the backend store", async ({ page }) => {
    await openConnectedApp(page);

    await page.getByRole("tab", { name: "Memory" }).click();
    const marker = `e2e-marker-${Date.now()}`;
    await page.getByLabel("Command input").fill(`remember that ${marker}`);
    await page.getByLabel("Send").click();

    await expect(page.locator(".response-panel")).toContainText("[Memory stored:", {
      timeout: 20000,
    });
  });
});
