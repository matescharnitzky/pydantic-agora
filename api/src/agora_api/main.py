from fastapi import FastAPI

from agora_api.api.deps import get_settings
from agora_api.api.main import api_router
from agora_api.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Agora API", version="0.1.0")
    app.include_router(api_router)
    if settings is not None:
        app.dependency_overrides[get_settings] = lambda: settings
    return app
