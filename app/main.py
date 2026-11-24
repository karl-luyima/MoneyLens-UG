
"""Main FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.categories import router as categories_router
from app.api.insights import router as insights_router
from app.api.transactions import router as transactions_router
from app.api.uploads import router as uploads_router
from app.api.users import router as users_router
from app.core.config import settings
from app.core.logging_config import configure_logging

# Initialize structured logging.
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Personal finance insights platform for Ugandan mobile money users.",
    version="1.0.0",
)

# Configure Cross-Origin Resource Sharing (CORS).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# Register API routers.
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    """Check whether the API is running."""
    logger.info("API root endpoint accessed")

    return {
        "message": "Welcome to MoneyLens UG API",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Check API health."""
    logger.info("API health check requested")

    return {"status": "healthy"}
docs/deployment.md