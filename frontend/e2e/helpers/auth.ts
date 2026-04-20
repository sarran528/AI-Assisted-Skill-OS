import type { Page } from "@playwright/test";

export async function registerViaUi(page: Page, email: string, password: string) {
  await page.goto("/register");
  await page.getByTestId("email").fill(email);
  await page.getByTestId("password").fill(password);
  await page.getByTestId("register-btn").click();
}
