---
title: Architecture
---

```mermaid
flowchart LR
    Frontend["Frontend"] -->|Health| API["API"]
    API -->|Enqueue| Postgres[("Postgres")]
    Postgres -->|Dequeue| Worker["Worker"]
    pgAdmin -->|Inspect| Postgres
    API -.->|Traces| Logfire["Logfire"]
    Worker -.->|Traces| Logfire
```

| Component | Role | Technology |
| --------- | ---- | ---------- |
| Frontend service | Presents the user interface. | [Next.js](https://nextjs.org/), [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Tailwind CSS](https://tailwindcss.com/), [shadcn/ui](https://ui.shadcn.com/) (configured) |
| API service | Validates requests and enqueues workflows. | [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/), [Uvicorn](https://www.uvicorn.org/) |
| Worker service | Runs workflows and model generation. | [Python](https://www.python.org/), [DBOS](https://docs.dbos.dev/), [Pydantic AI](https://pydantic.dev/docs/ai/) |
| Database | Stores workflow state. | [PostgreSQL](https://www.postgresql.org/) |
| Database administration | Inspects the database. | [pgAdmin](https://www.pgadmin.org/) |
| Observability | Collects and inspects traces. | [Logfire](https://logfire.pydantic.dev/) |

The API validates generation requests and enqueues portable JSON without importing worker code.
The worker constructs an explicit Pydantic AI `Agent`; `DBOSDurability` checkpoints model calls.
An output function supplies the caller's JSON Schema and validates the returned JSON before a
result is saved. API and worker validate their own copies of the HTTP/queue contract.

Workflow inputs and final results remain portable JSON. Internal Pydantic AI checkpoints use
DBOS's native Python serialization to preserve typed model responses. Completed model steps are
reused on recovery; interruption before a step is recorded can repeat an external model call.
Recovery across changed worker application versions is not established by same-version restart
tests. Agent telemetry excludes prompt/output and binary content. Keep execution local/private;
application cancellation and per-run call budgets are not implemented.
