import { expect, test } from "@playwright/test";

import { quickCompleteAssessment } from "./helpers/assessment";
import { registerViaUi } from "./helpers/auth";
import { mockFirstTenApis } from "./helpers/api";

test("roadmap exposes timeline, parameters, and support resources", async ({ page }) => {
  await mockFirstTenApis(page);

  await registerViaUi(page, `roadmap-${Date.now()}@example.com`, "TestPass123!");
  await page.getByTestId("start-assessment").click();
  await quickCompleteAssessment(page);
  await page.getByTestId("grounding-submit").click();
  await page.getByTestId("generate-roadmap").click();

  await page.getByTestId("view-roadmap-btn").click();
  await expect(page).toHaveURL("/roadmap/drawing");
  await expect(page.getByTestId("roadmap-screen")).toBeVisible();
  await expect(page.getByTestId("roadmap-timeline")).toBeVisible();

  await page.getByTestId("toggle-params").click();
  await expect(page.getByTestId("params-panel")).toBeVisible();

  await page.getByTestId("open-support-panel").click();
  await page.getByTestId("support-tab-resources").click();
  await expect(page.getByTestId("resource-list")).toContainText("Practice contour lines");
});
