# Task: `decision`

Answer named boolean, choice, and rubric questions about text using Jev through an Agent and DBOS checkpoints.

Submit `text` and `questions` to `decide`. Each question has a `type` and optional `question` wording (defaults to its name). Choices require 2–255 unique `options`; rubrics require 2–10 described `levels`, numbered from zero. Results are keyed by question name in `answers`: booleans include `value` and `probability_yes`; choices include `value`, `confidence`, and `probabilities`; rubrics also include `expected_score`. Boolean values use a 0.5 threshold; rubric values are the nearest level, rounding halves up. Probabilities and confidence are model estimates, not measured accuracy.

Requires `TYPESAFE_API_KEY` in the worker. Uses the moving `jev-latest` alias without a generative fallback. Free-form text and arbitrary JSON Schemas are not supported.

References: [TypeSafe (Jev)](https://pydantic.dev/docs/ai/models/typesafe/), [Decision models](https://pydantic.dev/docs/ai/models/decision/).
