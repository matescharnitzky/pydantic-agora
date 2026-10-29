# User scenarios

See the [root README](../../../README.md#development) for setup and test commands.

| Scenario | What it checks |
| --- | --- |
| [Worker crash and restart](recovery.spec.ts) | Submit a workflow, wait until it is running, kill the worker, confirm the workflow remains retrievable, restart the worker, and verify the same workflow completes with the expected result. |
| [Cancel running work](policies.spec.ts) | A user cancels a running workflow and can retrieve its saved failure; repeated cancellation is safe. |
| [Cancel queued work](policies.spec.ts) | A workflow cancelled while the worker is stopped stays cancelled after the worker starts again; unknown workflow IDs return 404. |
| [Bounded retry](policies.spec.ts) | A transient failure recovers within its call budget, and cancelling an already completed workflow preserves its result. |
