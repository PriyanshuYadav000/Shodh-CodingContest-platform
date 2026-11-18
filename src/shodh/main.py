from fastapi import FastAPI

from shodh.config.settings import settings
from shodh.routes.health_routes import router as health_router
from shodh.routes.auth_routes import router as auth_router



app = FastAPI(
    title=settings.app_name,
    description="Backend API for Shodh Coding Contest Platform",
    version="0.1.0",
    debug=settings.debug
)


app.include_router(
    health_router,
    prefix=settings.api_v1_prefix
)

app.include_router(
    auth_router,
    prefix=settings.api_v1_prefix
)


@app.get("/")
def root():

    return {
        "message": "Shodh Coding Contest Platform API",
        "status": "running"
    }

from shodh.routes.organization_routes import (
    router as organization_router
)

app.include_router(
    organization_router,
    prefix=settings.api_v1_prefix
)