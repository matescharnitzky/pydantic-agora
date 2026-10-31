import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, ClassVar

from pydantic import BaseModel, JsonValue, ValidationError
from pydantic_ai import Tool


class Task[InputT: BaseModel, OutputT: BaseModel](ABC):
    """Define a task's typed inputs, outputs, and execution contract."""

    id: ClassVar[str]
    description: ClassVar[str]
    input_model: type[InputT]
    output_model: type[OutputT]

    @abstractmethod
    def run(self, inputs: InputT) -> OutputT:
        """Implement task logic using an already validated input model."""
        ...

    def metadata(self) -> dict[str, JsonValue]:
        """Describe the task and its schemas for PostgreSQL catalog and API discovery."""
        return {
            "id": self.id,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
            "output_schema": self.output_model.model_json_schema(),
        }

    @classmethod
    def as_tool(
        cls, executor: Callable[[str, dict[str, JsonValue]], dict[str, JsonValue]]
    ) -> Tool[Any]:
        """Expose the existing contracts, delegating execution to a durable caller."""

        async def invoke(**inputs: JsonValue) -> dict[str, JsonValue]:
            try:
                validated = cls.input_model.model_validate(inputs)
                result = await asyncio.to_thread(
                    executor, cls.id, validated.model_dump(mode="json")
                )
                return cls.output_model.model_validate(result).model_dump(mode="json")
            except ValidationError:
                raise ValueError("Invalid task data") from None

        tool = Tool.from_schema(
            invoke,
            name=cls.id,
            description=cls.description,
            json_schema=cls.input_model.model_json_schema(),
            sequential=True,
        )
        tool.function_schema.return_schema = cls.output_model.model_json_schema()
        return tool
