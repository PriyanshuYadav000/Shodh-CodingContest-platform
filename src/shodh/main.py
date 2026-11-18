from fastapi import FastAPI

from shodh.config.settings import settings
from shodh.routes.auth_routes import router as auth_router
from shodh.routes.contest_routes import router as contest_router
from shodh.routes.health_routes import router as health_router
from shodh.routes.organization_routes import router as organization_router
from shodh.routes.participation_routes import router as participation_router
from shodh.routes.problem_routes import router as problem_router
from shodh.routes.submission_routes import router as submission_router

app = FastAPI(
    title=settings.app_name,
    description="Backend API for Shodh Coding Contest Platform",
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(organization_router, prefix=settings.api_v1_prefix)
app.include_router(contest_router, prefix=settings.api_v1_prefix)
app.include_router(participation_router, prefix=settings.api_v1_prefix)
app.include_router(problem_router, prefix=settings.api_v1_prefix)
app.include_router(submission_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root():
    return {
        "message": "Shodh Coding Contest Platform API",
        "status": "running",
    }
