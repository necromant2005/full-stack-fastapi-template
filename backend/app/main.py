import logging
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings

FRONTEND_DIR = Path(__file__).parent / "frontend"
logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.FASTAPI_ENV != "development":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_HOST],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_authorization_denial(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    response = await call_next(request)
    if response.status_code == 403:
        route = request.scope.get("route")
        route_path = getattr(route, "path", "<unmatched>")
        if request.url.path.startswith(
            settings.API_V1_STR
        ) and not route_path.startswith(settings.API_V1_STR):
            route_path = f"{settings.API_V1_STR}{route_path}"
        logger.warning(
            "authorization_denied method=%s route=%s",
            request.method,
            route_path,
        )
    return response


app.include_router(api_router, prefix=settings.API_V1_STR)
app.frontend("/", directory=FRONTEND_DIR)
