"""Vercel-optimized FastAPI entry point for the Retina API.

This version handles missing heavy dependencies gracefully and provides
fallback responses for functionality that requires them.
"""

import os
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configure logging for Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Matic Retina API (Vercel)",
    version="0.1.0",
    description="Lightweight API deployment for Vercel with fallback functionality",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
_env_origins = os.environ.get("CORS_ORIGINS", "")
_extra_origins = [o.strip() for o in _env_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "Retina API",
        "version": "0.1.0",
        "deployment": "vercel-lite",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health():
    return {"status": "ok", "deployment": "vercel-lite"}

# ── Import routers with fallback handling ────────────────────────────────────

try:
    from api.routers import auth
    app.include_router(auth.router)
    logger.info("Auth router loaded successfully")
except ImportError as e:
    logger.warning("Auth router failed to load: %s", e)
    
    @app.get("/auth/fallback")
    def auth_fallback():
        return {"error": "Auth functionality not available in lite deployment"}

try:
    from api.routers import admin
    app.include_router(admin.router)
    logger.info("Admin router loaded successfully")
except ImportError as e:
    logger.warning("Admin router failed to load: %s", e)

# Load projects router with careful handling
try:
    from api.routers import projects
    app.include_router(projects.router)
    logger.info("Projects router loaded successfully")
except ImportError as e:
    logger.warning("Projects router failed to load: %s", e)
    
    @app.get("/projects/fallback")
    def projects_fallback():
        return {"error": "Projects functionality not available in lite deployment"}

# Load export router with fallback
try:
    from api.routers import export
    app.include_router(export.router)
    logger.info("Export router loaded successfully")
except ImportError as e:
    logger.warning("Export router failed to load: %s", e)
    
    @app.get("/projects/{project_id}/export/status")
    def export_fallback(project_id: str):
        return {
            "status": "unavailable",
            "message": "PDF export not available in lite deployment",
            "project_id": project_id
        }

# ── Debug endpoints with safe imports ─────────────────────────────────────────

@app.get("/debug/info")
def debug_info():
    """Debug endpoint: show deployment info and available features."""
    return {
        "deployment": "vercel-lite",
        "python_version": os.sys.version,
        "environment": os.environ.get("VERCEL_ENV", "unknown"),
        "features": {
            "pdf_export": False,
            "screenshot_capture": False,
            "heavy_analysis": False
        }
    }

@app.get("/debug/screenshot")
async def debug_screenshot():
    """Debug endpoint: screenshot functionality disabled in lite deployment."""
    return {
        "error": "Screenshot functionality not available in lite deployment",
        "status": "disabled",
        "suggestion": "Use full deployment for screenshot features"
    }

# ── Fallback for missing functionality ───────────────────────────────────────

@app.exception_handler(ImportError)
async def import_error_handler(request, exc):
    logger.error("Import error in request %s: %s", request.url, exc)
    return HTTPException(
        status_code=503,
        detail="Service temporarily unavailable due to missing dependencies"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
