---
title: DBOS recovery decision
---

## Decision

Proceed with DBOS for the local, single-worker foundation. Saved step results survive process
termination and are reused on restart. External calls require their own idempotency strategy;
DBOS alone does not make an external effect exactly once.

## Evidence

On 2026-10-28, six automated PostgreSQL tests passed with DBOS 2.31.1 and Python 3.13.
They ran the production workflow with test-only HTTP effects and crash barriers, a separate
API process, and an isolated DBOS schema per case. The controlled HTTP service stayed alive
while the worker was killed with SIGKILL and restarted using the same executor and version.

| Interruption / failure | Saved add steps before crash | HTTP calls | Applied effects | Outcome |
|---|---:|---:|---:|---|
| Before first step | 0 | 1 | 1 | Workflow restarted and completed |
| During first step, before effect | 0 | 1 | 1 | Unfinished step ran again |
| After saved add, before double | 1 | 1 | 1 | Add result reused; double completed |
| After effect, before step save; idempotent service | 0 | 2 | 1 | Repeated key detected and deduplicated |
| Same gap; non-idempotent service | 0 | 2 | 2 | Duplicate effect demonstrated |
| First HTTP call returns 503 | — | 2 | 1 | Configured step retry succeeded |

Every case retrieved the final result through the API, including after worker restart.
Saved DBOS step outputs were `[5, 10]`; the API returned `value=10`, `branch=doubled`.
The effect-gap cases recorded one duplicate call each, using the same workflow/step key.

## Conditions and limits

- Recovery reruns workflow code from the beginning; recorded steps supply their saved outputs.
  Put externally meaningful work inside steps and preserve deterministic step order.
- The tested restart preserves the executor ID, application name, version, and database schema.
  DBOS's [recovery guidance](https://docs.dbos.dev/production/workflow-recovery) requires an
  explicit strategy for distributed executors. Multi-worker failover and code-version upgrades
  are outside this evidence; do not replace the worker with incompatible workflow code.
- A crash can happen after an upstream effect succeeds but before DBOS saves the result.
  Use a stable operation key and an upstream service that durably deduplicates it. The test
  service only retains keys for its lifetime; its own crash recovery was not tested.
- These tests simulate process loss, not PostgreSQL loss, network partitions, or disk failure.
  Recovery still requires the database and a compatible worker to become available.
- The retry test explicitly enables three attempts. Retries are not automatically safe for
  non-idempotent calls. Durable retries and duplicate effects are separate concerns.
- Monty state, suspended workflow, source persistence, and host-call replay remain Phase 4 work.

No architecture change is required for the tested local scope. Capability integrations must
specify idempotency and version compatibility before exposing side-effecting upstream calls.
See the [README](../README.md) for reproduction commands and [architecture](architecture.md)
for the service boundary.
