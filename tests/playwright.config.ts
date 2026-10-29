import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./playwright",
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: process.env.FRONTEND_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      testIgnore: "**/scenarios/**",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "scenarios",
      testMatch: "**/scenarios/**/*.spec.ts",
      dependencies: ["chromium"],
      retries: 0,
      workers: 1,
    },
  ],
});
