import { randomUUID } from "node:crypto";
import type { APIRequestContext } from "@playwright/test";
import { test, expect } from "../fixtures.js";

test.use({ baseURL: process.env.API_BASE_URL ?? "http://localhost:8000" });

async function getWorkflow(request: APIRequestContext, id: string) {
  const response = await request.get(`/workflows/${id}`);
  expect(response.status()).toBe(200);
  return response.json();
}

const cancelled = { status: "failed", result: null, error: "Workflow cancelled or time limit exceeded" };

test("a user can cancel a running workflow and retrieve its saved failure", async ({ request }) => {
  const submitted = await request.post("/workflows", {
    data: { operation: "wait_then_add", inputs: { seconds: 5 } },
  });
  expect(submitted.status()).toBe(202);
  const { id } = await submitted.json();
  const path = `/workflows/${id}`;

  await expect.poll(async () => (await getWorkflow(request, id)).status,
    { timeout: 15_000 }).toBe("running");
  const response = await request.post(`${path}/cancel`);
  expect(response.status()).toBe(200);
  expect(await response.json()).toMatchObject({ id, ...cancelled });
  expect(await getWorkflow(request, id)).toMatchObject({ id, ...cancelled });
  expect(await (await request.post(`${path}/cancel`)).json()).toMatchObject({ id, ...cancelled });
});

test("a queued workflow stays cancelled after the worker starts again", async ({ request, worker }) => {
  await worker.stop();
  const submitted = await request.post("/workflows", {
    data: { operation: "add_then_scale", inputs: { left: 2, right: 3 } },
  });
  expect(submitted.status()).toBe(202);
  const { id } = await submitted.json();
  const path = `/workflows/${id}`;
  expect((await getWorkflow(request, id)).status).toBe("waiting");
  const response = await request.post(`${path}/cancel`);
  expect(response.status()).toBe(200);
  expect(await response.json()).toMatchObject({ id, ...cancelled });
  await worker.start();

  const next = await request.post("/workflows", {
    data: { operation: "add_then_scale", inputs: { left: 1, right: 2 } },
  });
  expect(next.status()).toBe(202);
  const nextId = (await next.json()).id;
  await expect.poll(async () => (await getWorkflow(request, nextId)).status,
    { timeout: 15_000 }).toBe("successful");
  expect(await getWorkflow(request, id)).toMatchObject({ id, ...cancelled });

  const missing = await request.post(`/workflows/${randomUUID()}/cancel`);
  expect(missing.status()).toBe(404);
});

test("a workflow with a transient failure finishes within its retry budget", async ({ request }) => {
  const submitted = await request.post("/workflows", {
    data: {
      operation: "wait_then_add", inputs: { seconds: 0, retry_once: true },
      limits: { max_calls: 3 },
    },
  });
  expect(submitted.status()).toBe(202);
  const { id } = await submitted.json();
  await expect.poll(async () => (await getWorkflow(request, id)).status,
    { timeout: 15_000 }).toBe("successful");
  const completed = await getWorkflow(request, id);
  expect(completed).toMatchObject({ id, result: { value: 5, branch: "unchanged" }, error: null });
  const response = await request.post(`/workflows/${id}/cancel`);
  expect(response.status()).toBe(200);
  expect(await response.json()).toMatchObject({ id, status: "successful", result: completed.result });
});
