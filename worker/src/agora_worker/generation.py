from typing import Annotated, cast

from jsonschema import Draft202012Validator
from jsonschema.protocols import Validator
from pydantic import JsonValue, WithJsonSchema
from pydantic_ai import Agent, ModelRetry
from pydantic_ai.durable_exec.dbos import DBOSDurability

from agora_worker.models import GenerationInputs, GenerationResult

agent = Agent[GenerationInputs, JsonValue](
    "openai-responses:gpt-5-mini",
    name="agora_generate_v1",
    deps_type=GenerationInputs,
    output_type=str,
    defer_model_check=True,
    capabilities=[DBOSDurability()],
)


def generate(inputs: GenerationInputs) -> GenerationResult:
    schema = inputs.output_schema

    def validated_output(output: Annotated[JsonValue, WithJsonSchema(schema)]) -> JsonValue:
        """Return the requested structured result."""
        assert schema is not None
        validator = cast(Validator, Draft202012Validator(schema))
        if not validator.is_valid(output):
            raise ModelRetry("Return JSON satisfying every constraint in the output schema.")
        return output

    result = agent.run_sync(
        inputs.prompt,
        instructions=inputs.instructions,
        model=f"openai-responses:{inputs.model}",
        output_type=str if schema is None else validated_output,
        deps=inputs,
    )
    return GenerationResult(output=result.output, model=result.response.model_name or inputs.model)


def generation_input_schema() -> dict[str, JsonValue]:
    """Publish schema validation rules as standard JSON Schema, without API-specific code."""
    schema = GenerationInputs.model_json_schema()
    schema["$defs"] = {
        "inline": {
            "if": {"type": "object"},
            "then": {
                "not": {"anyOf": [{"required": ["$ref"]}, {"required": ["$dynamicRef"]}]},
                "additionalProperties": {"$ref": "#/$defs/inline"},
            },
            "else": {
                "if": {"type": "array"},
                "then": {"items": {"$ref": "#/$defs/inline"}},
            },
        }
    }
    schema["properties"]["output_schema"] = {
        "anyOf": [
            {"type": "null"},
            {
                "type": "object",
                "allOf": [
                    {"$ref": "https://json-schema.org/draft/2020-12/schema"},
                    {"$ref": "#/$defs/inline"},
                ],
                "properties": {
                    "$schema": {"const": "https://json-schema.org/draft/2020-12/schema"}
                },
            },
        ],
        "default": None,
    }
    return schema
