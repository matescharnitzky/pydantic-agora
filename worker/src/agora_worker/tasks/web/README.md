# Task: `web`

Answer questions with an Agent, OpenAI-native WebSearchTool, and the worker-executed web_fetch_tool.

Submit `prompt` to `web`. Both tools are available; the model chooses calls, and OpenAI controls native search scheduling. Results include text, model text parts across the run with native citations (anchors are relative to each `text_parts[].text`), and successfully fetched textual pages. Function-tool fetches do not create provider-native citation anchors. Uses the existing OpenAI key and the `web-fetch` extra; no Researcher bundle or search service account. Upstream fetch defaults reject private/local URLs.

References: [Native tools](https://pydantic.dev/docs/ai/tools-toolsets/native-tools/), [Common tools](https://pydantic.dev/docs/ai/tools-toolsets/common-tools/), [Citations](https://pydantic.dev/docs/ai/core-concepts/citations/).
