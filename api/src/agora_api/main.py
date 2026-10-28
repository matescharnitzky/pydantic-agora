import logfire
from fastapi import FastAPI, Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from agora_api.api.main import api_router
from agora_api.config import settings
from agora_api.observability import configure_observability

configure_observability(settings)
app = FastAPI(title="Agora API", version="0.1.0")


@app.middleware("http")
async def trace_request(request: Request, call_next: RequestResponseEndpoint) -> Response:
    with logfire.span("HTTP request", http_method=request.method) as span:
        response = await call_next(request)
        span.set_attribute("http.status_code", response.status_code)
        if response.status_code >= 400:
            logfire.warn("Request rejected", status_code=response.status_code)
        return response


app.include_router(api_router)
