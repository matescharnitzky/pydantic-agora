import psycopg
from pydantic import TypeAdapter

from agora_api.models import Capability

capability_adapter = TypeAdapter(list[Capability])


def list_capabilities(connection: psycopg.Connection[tuple[object, ...]]) -> list[Capability]:
    row = connection.execute(
        "SELECT capabilities FROM agora.capability_registry WHERE application = %s",
        ("agora-worker",),
    ).fetchone()
    if row is None:
        raise psycopg.OperationalError("Capability registry unavailable")
    return capability_adapter.validate_python(row[0])


def validate_operation(operation: str, capabilities: list[Capability]) -> None:
    capability = next((item for item in capabilities if item.id == operation), None)
    if capability is None:
        raise ValueError("Unknown operation")
