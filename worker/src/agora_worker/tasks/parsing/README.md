# Task: `parsing`

Extract text from PDF/PNG/JPEG/WebP files with a dedicated Agent and DBOS checkpoints.

Submit `files` to `parse` using `{"kind": "inline", "media_type": "application/pdf", "data": "<base64>"}` or `{"kind": "url", "media_type": "image/png", "url": "https://..."}`. Files without readable text return `{"text": ""}`. The result is `{"text": "..."}` for later generation or decision tasks. Inline files persist with the run; URL content can change or expire. Extraction is model-backed, not deterministic OCR.

References: [Multimodal input](https://pydantic.dev/docs/ai/core-concepts/input/), [DBOS integration](https://pydantic.dev/docs/ai/durable_execution/dbos/).
