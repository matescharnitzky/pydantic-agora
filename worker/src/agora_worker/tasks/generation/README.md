# Task: `generation`

Generate text from a prompt and optional PDF/PNG/JPEG/WebP files using an Agent with DBOS checkpoints.

Use `files: [{"kind": "inline", "media_type": "application/pdf", "data": "<base64>"}]` or `{"kind": "url", "media_type": "image/png", "url": "https://..."}`. Inline content is stored with the run; remote content is read by the provider and may change or expire. This is model understanding, not a deterministic parser.

References: [Multimodal input](https://pydantic.dev/docs/ai/core-concepts/input/), [DBOS integration](https://pydantic.dev/docs/ai/durable_execution/dbos/).
