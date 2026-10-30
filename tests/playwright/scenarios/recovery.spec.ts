import { test, expect } from "../fixtures.js";

test.use({ baseURL: process.env.API_BASE_URL ?? "http://localhost:8000" });

test("a running workflow completes after the worker crashes and restarts", async ({ request, worker }) => {
  test.setTimeout(60_000);
  const input = { task: "wait_then_add", inputs: { seconds: 5 } };
  const submitted = await request.post("/workflows", { data: input });
  expect(submitted.status()).toBe(202);
  const { id } = await submitted.json();
  const path = `/workflows/${id}`;

  await test.step("Wait for the submitted workflow to start", async () => {
    await expect.poll(async () => {
      const response = await request.get(path);
      expect(response.status()).toBe(200);
      return (await response.json()).status;
    }, { timeout: 15_000 }).toBe("running");
  });

  await test.step("Crash the worker and confirm the workflow is still retrievable", async () => {
    await worker.crash();
    const response = await request.get(path);
    expect(response.status()).toBe(200);
    expect(await response.json()).toMatchObject({ id, status: "running", request: input, result: null });
  });

  await test.step("Restart the worker and retrieve the completed result", async () => {
    await worker.start();
    await expect.poll(async () => {
      const response = await request.get(path);
      expect(response.status()).toBe(200);
      return response.json();
    }, { timeout: 30_000 }).toMatchObject({
      id,
      status: "successful",
      request: input,
      result: { value: 5, branch: "unchanged" },
      error: null,
    });
  });
});
