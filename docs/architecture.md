---
title: Architecture
---

Next.js handles presentation, FastAPI owns HTTP contracts and validation, and the worker owns execution. PostgreSQL stores application state; pgAdmin provides database inspection.

```mermaid
flowchart LR
    Browser -->|HTTP| Frontend[Frontend · Next.js]
    Frontend -->|Readiness request| API[API · FastAPI]
    API -->|Readiness query| Postgres[(PostgreSQL)]
    Worker[Worker · Python] -->|Connectivity checks| Postgres
    pgAdmin[pgAdmin] -->|Inspect / query| Postgres
```

The current stack checks service and database readiness. The worker does not execute capabilities yet.

API and worker share a uv workspace and lockfile, but each container installs only its own runtime dependencies. They do not import each other's internals. Frontend dependencies use npm workspaces.
