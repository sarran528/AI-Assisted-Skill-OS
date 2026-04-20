import { expect, test } from "@playwright/test";

import { quickCompleteAssessment } from "./helpers/assessment";
import { registerViaUi } from "./helpers/auth";
import { mockFirstTenApis } from "./helpers/api";

test("assessment view supports flexible level flow and completion", async ({ page }) => {
  await mockFirstTenApis(page);

  await registerViaUi(page, `assessment-${Date.now()}@example.com`, "TestPass123!");
  await expect(page).toHaveURL("/dashboard");

  await page.getByTestId("start-assessment").click();
  await expect(page).toHaveURL("/assessment");
  await expect(page.getByTestId("assessment-screen")).toBeVisible();

  await page.getByTestId("level-card-3").click();
  await expect(page.locator("text=Level 3/6")).toBeVisible();

  await page.getByTestId("submit-response").click();
  await expect(page.locator("text=Question 2 / 10")).toBeVisible();

  await quickCompleteAssessment(page);
  await expect(page).toHaveURL("/dashboard");
});
