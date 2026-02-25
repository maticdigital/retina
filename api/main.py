"""FastAPI entry point for the Retina API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import admin, auth, export, projects

app = FastAPI(
    title="Matic Retina API",
    version="0.1.0",
    description="API layer between React frontend and Retina analysis engine",
)

# ── CORS — allow the React dev server ─────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(admin.router)
app.include_router(export.router)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/screenshot")
async def debug_screenshot():
    """Debug endpoint: test screenshot capture from within uvicorn."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from retina.config import Settings
    from retina.clients.screenshot import ScreenshotClient

    settings = Settings()
    client = ScreenshotClient(settings, use_subprocess=True)
    try:
        result = await client.capture("http://spekit.com", "spekit_debug_uvicorn")
        vp_path = result.viewport
        vp_size = os.path.getsize(vp_path) if vp_path and os.path.exists(vp_path) else 0
        return {"viewport": vp_path, "viewport_size": vp_size, "full_page": result.full_page}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await client.close()
