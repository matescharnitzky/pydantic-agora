import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { test as base, expect } from "@playwright/test";

const exec = promisify(execFile);

async function docker(...args: string[]): Promise<string> {
  const { stdout } = await exec("docker", args, { timeout: 15_000 });
  return stdout.trim();
}

type Worker = {
  crash(): Promise<void>;
  stop(): Promise<void>;
  start(): Promise<void>;
};

export const test = base.extend<{ worker: Worker }>({
  worker: async ({}, use) => {
    const project = process.env.COMPOSE_PROJECT_NAME ?? "agora";
    const output = await docker(
      "ps", "--all",
      "--filter", `label=com.docker.compose.project=${project}`,
      "--filter", "label=com.docker.compose.service=worker",
      "--format", "{{.ID}}",
    );
    const containers = output.split("\n").filter(Boolean);
    expect(containers, "Start the local stack with exactly one worker before running scenarios").toHaveLength(1);
    const id = containers[0];
    expect(await docker("inspect", "--format", "{{.State.Running}}", id)).toBe("true");
    const worker: Worker = {
      async crash() { await docker("kill", "--signal", "KILL", id); },
      async stop() { await docker("stop", "--time", "10", id); },
      async start() { await docker("start", id); },
    };
    try {
      await use(worker);
    } finally {
      await worker.start();
      await expect.poll(() => docker("inspect", "--format", "{{.State.Running}}", id)).toBe("true");
    }
  },
});

export { expect } from "@playwright/test";
