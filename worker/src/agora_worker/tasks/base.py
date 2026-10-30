from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel, JsonValue


class Task[InputT: BaseModel, OutputT: BaseModel](ABC):
    """Define the typed execution contract shared by catalog discovery and workflows."""

    id: ClassVar[str]
    description: ClassVar[str]
    input_model: type[InputT]
    output_model: type[OutputT]

    @abstractmethod
    def run(self, inputs: InputT) -> OutputT:
        """Execute with validated inputs and return the declared output model.

        Failures propagate to the calling workflow; implementations may perform external I/O.
        """
        ...

    def metadata(self) -> dict[str, JsonValue]:
        """Build catalog metadata and JSON schemas for API discovery without running the task."""
        return {
            "id": self.id,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
            "output_schema": self.output_model.model_json_schema(),
        }
