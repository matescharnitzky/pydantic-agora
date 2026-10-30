from typing import cast

import psycopg
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from jsonschema.protocols import Validator
from pydantic import TypeAdapter

from agora_api.models import Capability, WorkflowRequest

capability_adapter = TypeAdapter(list[Capability])


def list_capabilities(connection: psycopg.Connection[tuple[object, ...]]) -> list[Capability]:
    row = connection.execute(
        "SELECT capabilities FROM agora.capability_registry WHERE application = %s",
        ("agora-worker",),
    ).fetchone()
    if row is None:
        raise psycopg.OperationalError("Capability registry unavailable")
    return capability_adapter.validate_python(row[0])


def validate_request(request: WorkflowRequest, capabilities: list[Capability]) -> None:
    capability = next((item for item in capabilities if item.id == request.operation), None)
    if capability is None:
        raise ValueError("Unknown operation")
    try:
        validator = cast(Validator, Draft202012Validator(capability.input_schema))
        validator.validate(request.inputs)
    except ValidationError:
        raise ValueError("Inputs do not match the capability schema") from None
