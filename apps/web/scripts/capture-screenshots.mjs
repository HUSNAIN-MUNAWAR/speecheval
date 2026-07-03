import { chromium } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const baseUrl = process.env.SPEECHEVAL_WEB_URL ?? "http://127.0.0.1:3000";
const apiBaseUrl = process.env.SPEECHEVAL_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
const outputDirectory = path.resolve("../../docs/assets/screenshots");

async function fetchRunDetailRoute() {
  const response = await fetch(`${apiBaseUrl}/evaluation-runs`);
  if (!response.ok) {
    throw new Error(`Unable to load evaluation runs from ${apiBaseUrl}.`);
  }
  const payload = await response.json();
  const eligibleRuns = payload.items.filter(
    (run) => ["COMPLETED", "PARTIAL"].includes(run.status) && run.processed_items > 1,
  );
  let detailRun = null;
  for (const run of eligibleRuns) {
    const samplesResponse = await fetch(`${apiBaseUrl}/evaluation-runs/${run.id}/samples`);
    if (!samplesResponse.ok) {
      continue;
    }
    const samples = await samplesResponse.json();
    if (samples.total > 0) {
      detailRun = run;
      break;
    }
  }
  detailRun ??= eligibleRuns.find((run) => run.regression_decision) ?? eligibleRuns[0] ?? null;
  return detailRun
    ? {
        name: "run-control-center",
        route: `/runs/${detailRun.id}`,
        waitForText: "Run Control Center",
      }
    : null;
}

const routes = [
  {
    name: "overview",
    route: "/",
    waitForText: "Quality signals, not guesswork.",
  },
  {
    name: "projects",
    route: "/projects",
    waitForText: "Multilingual Narration Regression",
  },
  {
    name: "runs",
    route: "/runs",
    waitForText: "Evaluation runs",
  },
  {
    name: "compare",
    route: "/compare",
    waitForText: "Compare eligible runs",
    afterLoad: async (page) => {
      await page.waitForFunction(() => {
        const button = [...document.querySelectorAll("button")].find((value) =>
          value.textContent?.includes("Compare eligible runs"),
        );
        return button && !button.hasAttribute("disabled");
      });
      await page.getByRole("button", { name: "Compare eligible runs" }).click();
      await page
        .locator("text=/STRICTLY_COMPARABLE|COMPARABLE_WITH_WARNINGS|NOT_COMPARABLE/")
        .first()
        .waitFor({ state: "visible" });
    },
  },
  {
    name: "system",
    route: "/system",
    waitForText: "Platform operations",
  },
];

await fs.mkdir(outputDirectory, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1024 } });
const runDetailRoute = await fetchRunDetailRoute();
if (runDetailRoute) {
  routes.splice(3, 0, runDetailRoute);
}

for (const { name, route, waitForText, afterLoad } of routes) {
  await page.goto(new URL(route, baseUrl).toString(), {
    waitUntil: "networkidle",
  });
  await page.getByText(waitForText).first().waitFor({ state: "visible" });
  if (afterLoad) {
    await afterLoad(page);
  }
  await page.waitForTimeout(400);
  await page.screenshot({
    path: path.join(outputDirectory, `${name}.png`),
    fullPage: true,
  });
}

await browser.close();
console.log(`Captured ${routes.length} screens in ${outputDirectory}`);
