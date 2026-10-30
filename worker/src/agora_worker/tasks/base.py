from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel, JsonValue


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
