import { expect, test } from "@playwright/test";

test("documentation renders Markdown, links, diagrams, and search", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Documentation", exact: true }).click();
  await expect(page.getByRole("heading", { name: /^Agora\b/, level: 1 })).toBeVisible();
  await expect(page.getByRole("heading", { name: /^Run locally\b/, level: 2 })).toBeVisible();
  await expect(page.locator("main")).toContainText("make up");
  const readmeSearch = await page.request.get("/api/search?query=1Password");
  expect(readmeSearch.ok()).toBeTruthy();
  expect(await readmeSearch.json()).toEqual(expect.arrayContaining([expect.objectContaining({ url: expect.stringMatching(/^\/docs(?:#|$)/) })]));
  await page.getByRole("link", { name: "Architecture", exact: true }).first().click();
  await expect(page).toHaveURL(/\/docs\/architecture$/);
  await expect(page.getByRole("heading", { name: "Architecture", exact: true })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Role", exact: true })).toBeVisible();
  await expect(page.getByLabel("Architecture diagram").locator("svg")).toBeVisible();
  const alternateOrigin = new URL(page.url());
  if (["localhost", "127.0.0.1"].includes(alternateOrigin.hostname)) {
    alternateOrigin.hostname = alternateOrigin.hostname === "localhost" ? "127.0.0.1" : "localhost";
    await page.goto(alternateOrigin.href);
    await expect(page.getByLabel("Architecture diagram").locator("svg")).toBeVisible();
  }
  const search = await page.request.get("/api/search?query=PostgreSQL");
  expect(search.ok()).toBeTruthy();
  expect(await search.json()).toEqual(expect.arrayContaining([expect.objectContaining({ url: expect.stringContaining("/docs/architecture") })]));
  await page.getByRole("button", { name: /Search/i }).first().click();
  const dialog = page.getByRole("dialog");
  await dialog.locator("input").fill("PostgreSQL");
  await expect(dialog).toContainText("Architecture");
  await page.keyboard.press("Escape");
  await page.getByRole("link", { name: "Development tooling", exact: true }).first().click();
  await expect(page).toHaveURL(/\/docs\/development-tooling$/);
  await expect(page.getByRole("heading", { name: "Development tooling", exact: true })).toBeVisible();
  await expect(page.getByRole("table")).toContainText("Code quality");
  await page.goto("/docs/does-not-exist");
  await expect(page.getByText("This page could not be found.")).toBeVisible();
});
