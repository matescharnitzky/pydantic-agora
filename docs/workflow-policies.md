---
title: Workflow policies
---

Only registered operations run. API and worker validate inputs independently; results must
match their Pydantic model and contain finite numbers. Credentials are process settings,
never workflow arguments. This runtime is for local or private use and has no authentication.

Every request may include `limits`:

| Field | Default | Allowed | Meaning |
| --- | ---: | --- | --- |
| `timeout_seconds` | 10 | 0.1–30 | Deadline starting when the worker dequeues the workflow |
| `max_calls` | 4 | 1–4 | Maximum reserved step attempts |

`wait_then_add` accepts `seconds` from 0 to 5 and `retry_once` (default `false`). It waits,
then adds 2 and 3. The wait reserves two attempts, and the add reserves one. Other steps
reserve one attempt each. An exhausted budget fails before the next step starts.

`POST /workflows/{id}/cancel` cancels a waiting or running workflow. Cancellation is safe to
repeat; completed workflows keep their outcomes. Cancellation and deadlines are cooperative:
an in-flight step may finish, but subsequent steps cannot start. They do not undo an external
action. Cancelled workflows remain retrievable with status `failed` and no final result.

Set `LOGFIRE_TOKEN` to export API and worker traces to Logfire. Workflow IDs connect requests,
steps, retries, and failures. Request bodies, settings, and results are excluded from app tracing.
