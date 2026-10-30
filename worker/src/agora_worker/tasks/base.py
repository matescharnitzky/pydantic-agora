from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel, JsonValue


class Task[InputT: BaseModel, OutputT: BaseModel](ABC):
    id: ClassVar[str]
    description: ClassVar[str]
    input_model: type[InputT]
    output_model: type[OutputT]

    @abstractmethod
    def run(self, inputs: InputT) -> OutputT: ...

    def metadata(self) -> dict[str, JsonValue]:
        return {
            "id": self.id,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
            "output_schema": self.output_model.model_json_schema(),
        }

    def call(self, inputs: dict[str, JsonValue]) -> dict[str, JsonValue]:
        validated_input = self.input_model.model_validate(inputs)
        result = self.run(validated_input)
        return self.output_model.model_validate(result).model_dump(mode="json")
