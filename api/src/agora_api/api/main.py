from fastapi import APIRouter

from agora_api.api.routes import health, orchestrations, runs, tasks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(tasks.router)
api_router.include_router(runs.router)

api_router.include_router(orchestrations.router)
