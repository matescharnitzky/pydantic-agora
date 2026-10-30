from fastapi import APIRouter

from agora_api.api.routes import health, runs, tasks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(tasks.router)
api_router.include_router(runs.router)
