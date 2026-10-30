from fastapi import APIRouter

from agora_api.models import Capability, GenerationInputs, GenerationResult

router = APIRouter(prefix="/capabilities", tags=["capabilities"])


@router.get("", response_model=list[Capability])
def list_capabilities() -> list[Capability]:
    return [
        Capability(
            id="generate",
            description="Generate text or JSON matching a caller-supplied schema.",
            input_schema=GenerationInputs.model_json_schema(),
            output_schema=GenerationResult.model_json_schema(),
            credentials=["OPENAI_API_KEY (worker)"],
            constraints=[
                "OpenAI Responses models only",
                "Inline JSON Schema draft 2020-12 schemas; references are not supported",
                "Provider-specific schema/model restrictions may cause execution to fail",
                "Local/private execution; no application cancellation or call-budget policy",
            ],
        )
    ]
