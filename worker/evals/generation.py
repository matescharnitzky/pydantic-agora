"""Live generation baseline; run explicitly with make test-models."""

from pydantic import JsonValue
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected

from agora_worker.generation import generate
from agora_worker.models import GenerationInputs

dataset = Dataset[GenerationInputs, JsonValue](
    name="generation-baseline",
    cases=[
        Case(
            name="text",
            inputs=GenerationInputs(prompt="Reply with exactly: hello"),
            expected_output="hello",
        ),
        Case(
            name="extraction",
            inputs=GenerationInputs(
                prompt="Extract the name from: Ada Lovelace.",
                output_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                    "additionalProperties": False,
                },
            ),
            expected_output={"name": "Ada Lovelace"},
        ),
        Case(
            name="classification",
            inputs=GenerationInputs(
                prompt="Classify: Please refund my order.",
                output_schema={
                    "type": "object",
                    "properties": {"category": {"enum": ["refund", "other"]}},
                    "required": ["category"],
                    "additionalProperties": False,
                },
            ),
            expected_output={"category": "refund"},
        ),
    ],
    evaluators=[EqualsExpected()],
)


if __name__ == "__main__":
    report = dataset.evaluate_sync(lambda inputs: generate(inputs).output, max_concurrency=1)
    report.print()
    if report.failures or any(
        not result.value for case in report.cases for result in case.assertions.values()
    ):
        raise SystemExit(1)
