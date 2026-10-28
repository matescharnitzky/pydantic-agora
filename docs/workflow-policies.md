---
title: Workflow policies
---

Only the three registered dummy operations run. API and worker independently validate typed
inputs; result models reject wrong types, missing fields, and non-finite numbers. The JSON
contract accepts no source code, import paths, credential values, or arbitrary function names.
Authentication remains Phase 8 work: use this runtime only locally or in private infrastructure.

## Limits and cancellation

Every request may include `limits`:

| Field | Default | Allowed | Meaning |
|---|---:|---|---|
| `timeout_seconds` | 10 | 0.1–30 | DBOS start-to-close deadline, beginning when dequeued |
| `max_calls` | 4 | 1–4 | Maximum reserved step attempts in the authored workflow |

Arithmetic inputs are integers within ±1,000,000. `wait_then_add` accepts `seconds` within
0–5 and optional `retry_once=false`; it waits, then adds 2 and 3. `retry_once=true` raises
one controlled transient error to demonstrate a retry. This step permits at most two attempts
and retries only that specific error. The budget reserves both attempts before entering it,
even when no retry occurs; the final add reserves one more. Other steps reserve one attempt
each and do not retry. Exceeding the budget fails before the next step starts.

Deadlines and `POST /workflows/{id}/cancel` use DBOS cooperative cancellation. A synchronous
step already in flight can finish and save its step result; subsequent steps cannot start,
and the workflow remains failed with no final result. This is not hard wall-clock preemption
or rollback of an external effect. Queue wait time is outside the start-to-close deadline.
The worker admits four concurrent workflows; cancelled in-flight calls occupy their slots
until they return. Future upstream integrations need bounded client timeouts as well.

Cancellation returns the saved workflow and is safe to repeat. Successful/failed completed
workflows retain their outcomes. Cancelled records remain retrievable after DBOS removes their
queue association. Errors expose only fixed messages: operation failure, exhausted call budget,
or cancellation/time limit. Raw worker exceptions remain internal.

## Credentials and traces

Credentials are process settings, not workflow arguments. No approved operation can read the
worker environment. The API logs request method/status and workflow IDs, not request bodies,
settings, results, or arbitrary client values. The worker logs approved step names, workflow
IDs, attempt numbers, latency, and failures. DBOS propagates the API's OpenTelemetry context
through PostgreSQL to worker workflow/step spans, including after a compatible restart.

Set `LOGFIRE_TOKEN` to send these spans to hosted Logfire. With no token, hosted export is
disabled; standard OTLP configuration can direct test traces to a local collector. Console
telemetry is disabled. Tests use a local OTLP collector, verify API/worker trace linkage and
retry events, and ensure a controlled worker-only secret is absent from client responses,
persisted workflows/step outputs, and captured trace payloads. This verifies the current
allowlist; adding upstream operations requires renewed credential and output review.

## Verification and rollout

See the [README](../README.md) for commands. `make test-policies` runs isolated real-PostgreSQL
checks for budget exhaustion, deadlines, waiting/running cancellation, retries, validation,
trace propagation, and secret isolation. Bruno covers malformed/denied inputs, exhausted
budgets, time limits, and cancellation over HTTP. Policy checks run on every CI change;
[recovery checks](dbos-recovery.md) remain in the broader suite.

Drain outstanding workflows before upgrading worker code. Compatible API defaults allow
previous requests without `limits`, but DBOS application-version matching still controls
recovery of workflows started by an older worker image. Monty restrictions and programmable
host-call policies belong to Phase 4.
