
"""Main FastAPI application entry point."""

from fastapi import FastAPI

from app.api.auth import router as auth_router
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


@app.get("/", tags=["Health"])
def root():
    """Check whether the API is running."""
    return {
        "message": "Welcome to MoneyLens UG API",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Check API health."""
    return {"status": "healthy"}
