"""
Main entry point for the Smart Municipal Complaint Management System
"""
import os
import logging
logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.core.config import settings
from src.core.database import engine, Base

# Import all models first (ensures SQLAlchemy resolves relationships)
import src.core.models_registry  # noqa: F401

# Import routers
from src.auth import router as auth_router
from src.users import router as users_router
from src.users.router.user_roles_router import router as user_roles_router
from src.roles import router as roles_router
from src.departments import router as departments_router
from src.problems import router as issues_router
from src.complaints import router as complaints_router
from src.votes import router as votes_router
from src.assignments import router as assignments_router
from src.notifications import router as notifications_router
from src.core.upload_router import router as upload_router

# Create database tables
Base.metadata.create_all(bind=engine)


def _migrate_sqlite_issues_resolved_image() -> None:
    """Add resolved_image column to issues when using existing SQLite DB."""
    if engine.dialect.name != "sqlite":
        return
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "issues" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("issues")}
    if "resolved_image" in cols:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE issues ADD COLUMN resolved_image VARCHAR"))

_migrate_sqlite_issues_resolved_image()


def _migrate_sqlite_issues_resolved_by_id() -> None:
    """Add resolved_by_id on issues (SQLite) for who set resolved/closed."""
    if engine.dialect.name != "sqlite":
        return
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "issues" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("issues")}
    if "resolved_by_id" in cols:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE issues ADD COLUMN resolved_by_id INTEGER"))


_migrate_sqlite_issues_resolved_by_id()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Smart Municipal Complaint Management System API"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(os.path.join(UPLOAD_DIR, "profiles"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "complaints"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "issues_resolved"), exist_ok=True)

# مسارات الرفع (/uploads/...) يجب تسجيلها قبل Mount الثابت — وإلا يأخذها StaticFiles وترد 405 على POST.
app.include_router(upload_router)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(user_roles_router)
app.include_router(roles_router)
app.include_router(departments_router)
app.include_router(issues_router)
app.include_router(complaints_router)
app.include_router(votes_router)
app.include_router(assignments_router)
app.include_router(notifications_router)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Smart Municipal Complaint Management System API",
        "version": settings.APP_VERSION
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

