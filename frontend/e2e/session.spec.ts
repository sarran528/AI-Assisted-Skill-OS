import { expect, test } from "@playwright/test";

import { quickCompleteAssessment } from "./helpers/assessment";
import { registerViaUi } from "./helpers/auth";
import { mockFirstTenApis } from "./helpers/api";

async function enterSession(page: import("@playwright/test").Page) {
  await registerViaUi(page, `session-${Date.now()}@example.com`, "TestPass123!");
  await page.getByTestId("start-assessment").click();
  await quickCompleteAssessment(page);
  await page.getByTestId("skill-drawing").click();
  await page.getByTestId("grounding-submit").click();
  await page.getByTestId("generate-roadmap").click();
  await page.getByTestId("enter-session").click();
  await expect(page).toHaveURL(/\/session\//);
}

test("session enforces protocol and opens support tools", async ({ page }) => {
  await mockFirstTenApis(page);
  await enterSession(page);

  await page.getByTestId("step-2-complete").click();
  await expect(page.getByTestId("protocol-warning")).toContainText("Follow protocol order");

  await page.getByTestId("step-1-complete").click();
  await page.getByTestId("step-2-complete").click();
  await page.getByTestId("step-3-complete").click();
  await page.getByTestId("step-4-complete").click();

  await page.getByTestId("evidence-upload").setInputFiles("e2e/fixtures/test-drawing.png");
  await page.getByTestId("upload-evidence-btn").click();
  await expect(page.getByTestId("evidence-uploaded")).toBeVisible();

  await page.getByTestId("open-support-panel").click();
  await expect(page.getByTestId("support-panel")).toBeVisible();
  await page.getByTestId("doubt-question").fill("How do I stabilize line confidence in step 2?");
  await page.getByTestId("ask-doubt-btn").click();
  await expect(page.getByTestId("doubt-answer-card")).toBeVisible();
  await page.getByTestId("support-close-btn").click();

  await page.getByTestId("complete-session").click();
  await page.getByTestId("confirm-complete").click();
  await expect(page.getByTestId("completion-message")).toContainText("Session complete");
});
