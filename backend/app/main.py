import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api.routes import (
    shows, episodes, artwork, publish, validation, catalog, auth, health
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables & storage dirs exist
    os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.STORAGE_LOCAL_DIR, "uploads"), exist_ok=True)
    os.makedirs(os.path.join(settings.STORAGE_LOCAL_DIR, "catalog"), exist_ok=True)
    await init_db()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Peblo TV Mini — CMS upload, atomic publish pipeline, and Netflix-style viewer catalogue.",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for local storage uploads & catalog
storage_dir = settings.STORAGE_LOCAL_DIR
os.makedirs(storage_dir, exist_ok=True)
app.mount("/api/v1/storage", StaticFiles(directory=storage_dir), name="storage")
app.mount("/storage", StaticFiles(directory=storage_dir), name="top_storage")

# Include Routers
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(shows.router, prefix=settings.API_V1_STR)
app.include_router(episodes.router, prefix=settings.API_V1_STR)
app.include_router(artwork.router, prefix=settings.API_V1_STR)
app.include_router(publish.router, prefix=settings.API_V1_STR)
app.include_router(validation.router, prefix=settings.API_V1_STR)
app.include_router(catalog.router, prefix=settings.API_V1_STR)

# Top-level direct alias for GET /catalog per specification
app.include_router(catalog.router)

@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/health",
        "catalog_url": "/catalog",
        "cms_api_prefix": settings.API_V1_STR
    }
