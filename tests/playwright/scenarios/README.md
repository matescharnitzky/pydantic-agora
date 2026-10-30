# User scenarios

See the [root README](../../../README.md#development) for setup and test commands.

| Scenario | What it checks |
| --- | --- |
| [Worker crash and restart](recovery.spec.ts) | Submit a run, wait until it is running, kill the worker, confirm the run remains retrievable, restart the worker, and verify the same run completes with the expected result. |
