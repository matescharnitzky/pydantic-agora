import base64
from typing import Annotated, ClassVar, Literal

from pydantic import Base64Bytes, BaseModel, ConfigDict, Field, HttpUrl, field_validator
from pydantic_ai import Agent, BinaryContent, DocumentUrl, ImageUrl
from pydantic_ai.durable_exec.dbos import DBOSDurability
from pydantic_ai.messages import UserContent

from agora_worker.tasks.base import Task

MediaType = Literal["application/pdf", "image/png", "image/jpeg", "image/webp"]


class InlineFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["inline"] = "inline"
    media_type: MediaType
    data: Base64Bytes = Field(description="Base64-encoded file content, saved with the run.")

    @field_validator("data", mode="before")
    @classmethod
    def validate_base64(cls, value: object) -> object:
        if not isinstance(value, str | bytes):
            raise ValueError("File data must be base64 text")
        try:
            decoded = base64.b64decode(value, validate=True)
        except ValueError:
            raise ValueError("File data must be valid base64") from None
        if not decoded:
            raise ValueError("File data must not be empty")
        return value


class RemoteFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["url"] = "url"
    media_type: MediaType
    url: HttpUrl


class GenerationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    prompt: str = Field(min_length=1)
    instructions: str = ""
    files: list[Annotated[InlineFile | RemoteFile, Field(discriminator="kind")]] = Field(
        default_factory=list[InlineFile | RemoteFile],
        description="PDFs and images. URLs must remain accessible to the provider until read.",
    )


class GenerationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    output: str


class GenerationTask(Task[GenerationInput, GenerationOutput]):
    id = "generate"
    description = "Generate text with an OpenAI model."
    input_model = GenerationInput
    output_model = GenerationOutput

    agent: ClassVar[Agent[GenerationInput, str]] = Agent(
        "openai-responses:gpt-5-mini",
        name="agora_generate_v1",
        deps_type=GenerationInput,
        output_type=str,
        defer_model_check=True,
        capabilities=[DBOSDurability()],
    )

    def run(self, inputs: GenerationInput) -> GenerationOutput:
        prompt: list[UserContent] = [inputs.prompt]
        for file in inputs.files:
            if isinstance(file, InlineFile):
                prompt.append(BinaryContent(data=file.data, media_type=file.media_type))
            elif file.media_type == "application/pdf":
                prompt.append(DocumentUrl(str(file.url), media_type=file.media_type))
            else:
                prompt.append(ImageUrl(str(file.url), media_type=file.media_type))
        result = self.agent.run_sync(
            prompt,
            instructions=inputs.instructions,
            deps=inputs,
        )
        return GenerationOutput(output=result.output)
