async function waitForRun(bru, id, { timeoutMs = 20_000 } = {}) {
  const deadline = Date.now() + timeoutMs;
  const url = bru.getEnvVar("baseUrl") + "/runs/" + id;
  let status = "waiting";

  while (Date.now() < deadline) {
    const remaining = deadline - Date.now();
    const response = await bru.sendRequest({ method: "GET", url, timeout: Math.max(1, remaining) });
    if (response.status !== 200) {
      throw new Error(`Run ${id} returned HTTP ${response.status}`);
    }
    const run = response.data;
    status = run.status;
    if (["successful", "failed"].includes(status)) return run;
    if (!["waiting", "running"].includes(status)) {
      throw new Error(`Run ${id} returned unexpected status: ${status}`);
    }
    const delay = Math.min(100, deadline - Date.now());
    if (delay > 0) await bru.sleep(delay);
  }

  throw new Error(`Run ${id} did not finish within ${timeoutMs} ms (last status: ${status})`);
}

module.exports = { waitForRun };
