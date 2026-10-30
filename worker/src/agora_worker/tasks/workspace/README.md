# Task: `workspace`

Answer questions over a read-only worker workspace with an Agent, LocalWorkspace, and explicit FileSystem tools.

Submit `prompt` to `workspace`. Compose mounts `tests/fixtures/workspace` at `/workspace`; change that mount to use your own trusted files. The result includes text and `files_requested` (reader calls, including missing-file attempts). No shell, writes, vector store, or Coder bundle. LocalWorkspace is not a sandbox; files can change between runs.

References: [FileSystem](https://pydantic.dev/docs/ai/harness/filesystem/), [Workspaces](https://pydantic.dev/docs/ai/core-concepts/workspace/).
