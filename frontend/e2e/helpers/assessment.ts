import type { Page } from "@playwright/test";

export async function quickCompleteAssessment(page: Page) {
  await page.getByTestId("quick-complete-assessment").click();
  await page.getByTestId("complete-assessment").click();
}
