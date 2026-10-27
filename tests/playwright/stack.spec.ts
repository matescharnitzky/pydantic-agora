import { expect, test } from "@playwright/test";

test("local shell reflects the running API and PostgreSQL readiness", async ({ page, request }) => {
  const response = await request.get(`${process.env.API_BASE_URL ?? "http://localhost:8000"}/ready`);
  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({ status: "ok", service: "api" });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Agora", exact: true })).toBeVisible();
  await expect(page.getByRole("status")).toHaveText("API and database are ready");
  await expect(page.getByText(/Not affiliated with or endorsed by Pydantic/)).toBeVisible();
});
