from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app import __version__
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.cameras import router as cameras_router
from app.api.router import router
from app.api.ws import get_websocket_manager, router as ws_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.realtime.service import get_realtime_service

logger = get_logger(__name__)

OPENAPI_TAGS = [
    {
        "name": "Authentication",
        "description": "User registration, login, JWT token management, and profile.",
    },
    {
        "name": "Cameras",
        "description": "Camera configuration and management. Write operations require Admin role.",
    },
    {
        "name": "Count Events",
        "description": "People counting events and daily summaries.",
    },
    {
        "name": "Real-time",
        "description": "WebSocket live count updates for dashboards.",
    },
    {
        "name": "Analytics",
        "description": "Aggregated people count analytics with date and camera filtering.",
    },
    {
        "name": "Users",
        "description": "User management. Admin only.",
    },
    {
        "name": "System",
        "description": "Health and system endpoints.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting %s v%s [%s]", settings.app_name, __version__, settings.app_env)

    get_websocket_manager()
    realtime = get_realtime_service()
    await realtime.start()

    yield

    await realtime.stop()
    logger.info("Shutting down %s", settings.app_name)


def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=settings.app_name,
        version=__version__,
        description=(
            "People Counting System API with JWT authentication.\n\n"
            "## Authentication\n"
            "1. Register via `POST /api/v1/auth/register` or login via `POST /api/v1/auth/login`\n"
            "2. Use the returned `access_token` in the `Authorization: Bearer <token>` header\n"
            "3. Refresh tokens via `POST /api/v1/auth/refresh`\n\n"
            "## Real-time Dashboard\n"
            "Connect via WebSocket: `ws://host/ws/live-counts?token=<access_token>`\n\n"
            "## Roles\n"
            "- **Admin**: Full access to all resources\n"
            "- **Viewer**: Read access to cameras, events, and summaries"
        ),
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )

    schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT access token obtained from `/auth/login` or `/auth/refresh`",
    }

    app.openapi_schema = schema
    return app.openapi_schema


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")
    app.include_router(cameras_router, prefix="/api/v1")
    app.include_router(router, prefix="/api/v1")
    app.include_router(ws_router)

    app.openapi = lambda: custom_openapi(app)

    return app


app = create_app()
