import { test, expect } from "../fixtures.js";

test.use({ baseURL: process.env.API_BASE_URL ?? "http://localhost:8000" });

test("an in-progress run completes after the worker crashes and restarts", async ({ request, worker }) => {
  test.setTimeout(60_000);
  const input = { inputs: { seconds: 5 } };
  const submitted = await request.post("/tasks/wait_then_add/runs", { data: input });
  expect(submitted.status()).toBe(202);
  const { id } = await submitted.json();
  const path = `/runs/${id}`;

  await test.step("Wait for the submitted run to start", async () => {
    await expect.poll(async () => {
      const response = await request.get(path);
      expect(response.status()).toBe(200);
      return (await response.json()).status;
    }, { timeout: 15_000 }).toBe("running");
  });

  await test.step("Crash the worker and confirm the run is still retrievable", async () => {
    await worker.crash();
    const response = await request.get(path);
    expect(response.status()).toBe(200);
    expect(await response.json()).toMatchObject({ id, status: "running", request: { task: "wait_then_add", ...input }, result: null });
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
      request: { task: "wait_then_add", ...input },
      result: { value: 5, branch: "unchanged" },
      error: null,
    });
  });
});
