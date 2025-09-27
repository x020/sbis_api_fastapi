"""
Main FastAPI application for SBIS API integration service.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.exceptions.handlers import create_exception_handlers
from app.utils.logger import get_logger, setup_logging, log_request_middleware
from config.config import get_settings

# Get settings
settings = get_settings()

# Setup logging
setup_logging()

# Get logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    logger.info("Starting SBIS API FastAPI application")

    # Startup tasks
    logger.info("Application startup completed")

    yield

    # Shutdown tasks
    logger.info("Application shutdown initiated")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    # Create FastAPI application
    app = FastAPI(
        title="SBIS API FastAPI",
        description="Integration service for Saby CRM",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.origins,
        allow_credentials=settings.cors.credentials,
        allow_methods=settings.cors.methods,
        allow_headers=settings.cors.headers,
    )

    # Add trusted host middleware
    if settings.environment == "production":
        allowed_hosts = [settings.domain.domain, f"*.{settings.domain.domain}"]
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )

    # Add request logging middleware
    app.middleware("http")(log_request_middleware)

    # Add exception handlers
    exception_handlers = create_exception_handlers()
    for exc_type, handler in exception_handlers.items():
        app.add_exception_handler(exc_type, handler)

    # Include API routes
    app.include_router(router, prefix="/api/v1")

    # Add root redirect
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        """Redirect root to API info."""
        return JSONResponse(
            content={
                "message": "SBIS API FastAPI Service",
                "docs": "/docs",
                "health": "/api/v1/health"
            }
        )

    # Add metrics endpoint (if enabled)
    if settings.redis.url != "redis://localhost:6379":
        @app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint."""
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    """
    Run the application using Uvicorn when executed directly.
    """
    import uvicorn

    logger.info(
        "Starting application with uvicorn",
        extra={
            "host": settings.server.host,
            "port": settings.server.port,
            "reload": settings.server.reload,
            "debug": settings.server.debug
        }
    )

    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        log_level=settings.logging.level.lower(),
        access_log=True
    )