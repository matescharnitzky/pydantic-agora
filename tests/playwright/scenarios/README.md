# User scenarios

These Playwright tests check user-visible behavior through HTTP or the browser,
without importing application internals. See the [root README](../../../README.md#development)
for setup and test commands.

| Scenario | What it checks |
| --- | --- |
| [Worker crash and restart](recovery.spec.ts) | Submit a workflow, wait until it is running, kill the worker, confirm the workflow remains retrievable, restart the worker, and verify the same workflow completes with the expected result. |

When adding scenarios:

- Name files `<subject>.spec.ts` and give each test a plain-language description of the expected behavior.
- Use `test.step` for meaningful actions and polling assertions for asynchronous results.
- Keep reusable setup, service control, and cleanup in [fixtures](../fixtures.ts); keep scenario-specific actions and assertions in the test.
- Restore services during fixture cleanup, including when a test fails. Scenarios run one at a time after browser checks.
- Add one brief entry here for each test case. Keep the executable test as the source of truth.
