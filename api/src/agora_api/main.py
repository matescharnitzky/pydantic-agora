from fastapi import FastAPI

from agora_api.api.main import api_router

app = FastAPI(title="Agora API", version="0.1.0")
app.include_router(api_router)
