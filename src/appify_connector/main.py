import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .appify.client import AppifyClient
from .config import get_settings
from .exceptions import AppifyConnectorError
from .routers import auth, health, me, objects, sors
from .session_store import SessionStore

logger = logging.getLogger("appify_connector")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    store = SessionStore(settings.redis_url, settings.session_ttl_seconds)
    client = AppifyClient(settings)
    app.state.session_store = store
    app.state.appify_client = client
    logger.info("appify-connector starting; redis=%s env=%s", settings.redis_url, settings.environment)
    try:
        yield
    finally:
        await store.close()
        logger.info("appify-connector stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    prefix = settings.path_prefix
    app = FastAPI(
        title="Appify Connector",
        version="0.1.0",
        description="REST gateway for Appify metadata.",
        lifespan=lifespan,
        docs_url=f"{prefix}/docs",
        redoc_url=f"{prefix}/redoc",
        openapi_url=f"{prefix}/openapi.json",
    )

    async def _root() -> dict:
        return {
            "service": "appify-connector",
            "version": "0.1.0",
            "docs": f"{prefix}/docs",
            "openapi": f"{prefix}/openapi.json",
        }

    app.add_api_route(prefix or "/", _root, methods=["GET"], include_in_schema=False)
    if prefix:
        app.add_api_route(f"{prefix}/", _root, methods=["GET"], include_in_schema=False)

    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )

    @app.exception_handler(AppifyConnectorError)
    async def _handle_app_error(request: Request, exc: AppifyConnectorError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL", "message": f"{type(exc).__name__}: {exc}"},
        )

    app.include_router(health.router, prefix=prefix)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(objects.router, prefix=prefix)
    app.include_router(sors.router, prefix=prefix)
    app.include_router(me.router, prefix=prefix)
    return app


app = create_app()
