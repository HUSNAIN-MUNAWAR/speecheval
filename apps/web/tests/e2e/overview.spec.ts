import { test, expect } from "@playwright/test";
test("shows explicit demo provenance", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Quality signals, not guesswork.")).toBeVisible();
  await expect(page.getByText("Demo Speech Lab · Demo Data")).toBeVisible();
});
