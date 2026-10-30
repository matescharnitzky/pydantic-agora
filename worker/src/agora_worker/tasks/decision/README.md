# Task: `decision`

Answer a yes/no question about text with Jev through an Agent and DBOS checkpoints.

Submit `text` and `question` to `decide`; the result contains `answer` and `probability_yes`. Requires `TYPESAFE_API_KEY` in the worker. Uses the moving `jev-latest` alias, without a generative fallback. Probabilities are model estimates, not measured accuracy. Choice and rubric inputs are not exposed yet.

References: [TypeSafe (Jev)](https://pydantic.dev/docs/ai/models/typesafe/), [Decision models](https://pydantic.dev/docs/ai/models/decision/).
