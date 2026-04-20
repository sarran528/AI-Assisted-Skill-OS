import { expect, test } from "@playwright/test";

import { quickCompleteAssessment } from "./helpers/assessment";
import { registerViaUi } from "./helpers/auth";
import { mockFirstTenApis } from "./helpers/api";

test("execution loop first 10 steps", async ({ page }) => {
  await mockFirstTenApis(page);

  // Step 1: Register.
  await registerViaUi(page, `test-${Date.now()}@example.com`, "TestPass123!");
  await expect(page).toHaveURL("/dashboard");

  // Step 2: Start assessment.
  await page.getByTestId("start-assessment").click();
  await expect(page).toHaveURL("/assessment");

  // Step 3-5: Complete all assessment levels.
  await quickCompleteAssessment(page);
  await expect(page).toHaveURL("/dashboard");

  // Step 6: Select skill.
  await page.getByTestId("skill-drawing").click();

  // Step 7: Submit grounding probes.
  await page.getByTestId("grounding-recognition-0").click();
  await page.getByTestId("grounding-submit").click();

  // Step 8: Generate roadmap and verify fingerprint indicator.
  await page.getByTestId("generate-roadmap").click();
  await expect(page.getByTestId("roadmap-fingerprint")).toBeVisible();

  // Step 9: Start practice session.
  await page.getByTestId("enter-session").click();
  await expect(page).toHaveURL(/\/session\//);

  // Step 10: Submit metrics via first step completion.
  await page.getByTestId("step-1-complete").click();
  await expect(page.getByTestId("metrics-sent")).toContainText("1");
});
