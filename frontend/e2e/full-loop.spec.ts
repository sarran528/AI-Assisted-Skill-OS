import { expect, test } from "@playwright/test";

import { quickCompleteAssessment } from "./helpers/assessment";
import { registerViaUi } from "./helpers/auth";
import { mockFirstTenApis } from "./helpers/api";

test("full execution loop with roadmap and support", async ({ page }) => {
  await mockFirstTenApis(page);

  await registerViaUi(page, `full-${Date.now()}@example.com`, "TestPass123!");
  await expect(page).toHaveURL("/dashboard");

  await page.getByTestId("start-assessment").click();
  await quickCompleteAssessment(page);

  await page.getByTestId("skill-drawing").click();
  await page.getByTestId("grounding-submit").click();
  await page.getByTestId("generate-roadmap").click();
  await expect(page.getByTestId("roadmap-fingerprint")).toBeVisible();

  await page.getByTestId("enter-session").click();
  await expect(page).toHaveURL(/\/session\//);

  await page.getByTestId("step-1-complete").click();
  await page.getByTestId("step-2-complete").click();
  await page.getByTestId("step-3-complete").click();
  await page.getByTestId("step-4-complete").click();

  await page.getByTestId("evidence-upload").setInputFiles("e2e/fixtures/test-drawing.png");
  await page.getByTestId("upload-evidence-btn").click();
  await expect(page.getByTestId("evidence-uploaded")).toBeVisible();

  await page.getByTestId("complete-session").click();
  await page.getByTestId("confirm-complete").click();
  await expect(page.getByTestId("completion-message")).toContainText("checkpoint passed");

  await page.getByTestId("view-roadmap-from-session").click();
  await expect(page.getByTestId("roadmap-screen")).toBeVisible();
  await page.getByTestId("open-support-panel").click();
  await expect(page.getByTestId("support-panel")).toBeVisible();
});
