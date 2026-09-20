"""FastAPI application factory."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.database.session import SessionLocal
from app.services.content_sync_service import sync_content
from app.utils.storage import ensure_storage_dirs, thumbnails_dir


def create_app() -> FastAPI:
    configure_logging()
    logger = get_logger(__name__)
    ensure_storage_dirs()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info("Starting %s v%s (env=%s)", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)
        if settings.AUTO_SEED_ON_STARTUP:
            try:
                with SessionLocal() as db:
                    sync_content(db, prune_missing_courses=settings.AUTO_SEED_PRUNE_MISSING)
            except Exception:  # noqa: BLE001
                logger.exception("Content sync failed on startup; continuing without it.")
        yield
        logger.info("Shutting down %s", settings.APP_NAME)

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Static thumbnails (course cover images).
    app.mount(
        settings.THUMBNAILS_URL_PREFIX,
        StaticFiles(directory=str(thumbnails_dir())),
        name="thumbnails",
    )

    @app.get("/", tags=["root"], summary="Service root")
    def root() -> dict[str, str]:
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": f"{settings.API_V1_PREFIX}/health",
        }

    return app


app = create_app()
