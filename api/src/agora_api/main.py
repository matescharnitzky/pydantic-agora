import logfire
from fastapi import FastAPI

from agora_api.api.main import api_router
from agora_api.config import settings

logfire.configure(
    service_name="agora-api",
    token=settings.logfire_token.get_secret_value() or None,
    send_to_logfire=bool(settings.logfire_token.get_secret_value()),
    console=False,
    inspect_arguments=False,
    data_dir="/tmp/agora-logfire-api",
)
app = FastAPI(title="Agora API", version="0.1.0")
logfire.instrument_fastapi(app, request_attributes_mapper=lambda _request, _attributes: None)
app.include_router(api_router)
