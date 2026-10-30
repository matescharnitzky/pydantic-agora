from fastapi import APIRouter

from agora_api.api.routes import health, tasks, workflows

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(tasks.router)
api_router.include_router(workflows.router)
