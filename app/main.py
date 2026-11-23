
"""Main FastAPI application entry point."""

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.categories import router as categories_router
from app.api.transactions import router as transactions_router
from app.api.uploads import router as uploads_router
from app.api.users import router as users_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Personal finance insights platform for Ugandan mobile money users.",
    version="1.0.0",
)


# Register API routers.
app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    users_router,
    prefix="/api/v1",
)

app.include_router(
    uploads_router,
    prefix="/api/v1",
)

app.include_router(
    transactions_router,
    prefix="/api/v1",
)

app.include_router(
    categories_router,
    prefix="/api/v1",
)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    """Check whether the API is running."""
    return {
        "message": "Welcome to MoneyLens UG API",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Check API health."""
    return {"status": "healthy"}
