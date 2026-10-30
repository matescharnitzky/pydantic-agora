from fastapi import APIRouter

from agora_api.api.deps import RegistryConnection
from agora_api.models import Capability
from agora_api.services import capabilities

router = APIRouter(prefix="/capabilities", tags=["capabilities"])


@router.get("", response_model=list[Capability])
def list_capabilities(connection: RegistryConnection) -> list[Capability]:
    return capabilities.list_capabilities(connection)
