import { expect, test } from "@playwright/test";

test("documentation renders Markdown, links, diagrams, and search", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Documentation", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Agora documentation", exact: true })).toBeVisible();
  await page.locator("main").getByRole("link", { name: "Architecture", exact: true }).click();
  await expect(page).toHaveURL(/\/docs\/architecture$/);
  await expect(page.getByRole("heading", { name: "Architecture", exact: true })).toBeVisible();
  await expect(page.getByLabel("Architecture diagram").locator("svg")).toBeVisible();
  await page.goto("/docs/development");
  await page.getByRole("link", { name: "configuration setup", exact: true }).click();
  await expect(page).toHaveURL(/\/docs\/configuration$/);
  const search = await page.request.get("/api/search?query=1Password");
  expect(search.ok()).toBeTruthy();
  expect(await search.json()).toEqual(expect.arrayContaining([expect.objectContaining({ url: expect.stringContaining("/docs/configuration") })]));
  await page.getByRole("button", { name: /Search/i }).first().click();
  const dialog = page.getByRole("dialog");
  await dialog.locator("input").fill("1Password");
  await expect(dialog).toContainText("Configuration");
  await page.keyboard.press("Escape");
  await page.goto("/docs/does-not-exist");
  await expect(page.getByText("This page could not be found.")).toBeVisible();
});
