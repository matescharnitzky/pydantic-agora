from fastapi import APIRouter

from agora_api.api.routes import capabilities, health, workflows

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(capabilities.router)
api_router.include_router(workflows.router)
