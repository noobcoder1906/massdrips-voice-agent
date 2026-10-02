"""
backend/main.py

VoxSales Multi-Tenant AI Voice Agent Platform API — Phase 9.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from backend.database import connect_to_mongo, close_mongo_connection, db_instance
from backend.ws.voice_ws import router as voice_router
from backend.routes.routes import tenant_router, lead_router, product_router
from backend.routes.campaigns import router as campaign_router
from backend.routes.smart import router as smart_router
from backend.routes.calls import router as calls_router
from backend.routes.webhooks import router as webhooks_router
from backend.campaigns.scheduler import scheduler_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → yield → shutdown."""
    await connect_to_mongo()
    scheduler_instance.start()
    yield
    scheduler_instance.stop()
    await close_mongo_connection()


app = FastAPI(
    title="VoxSales Public API",
    description="Multi-Tenant AI Voice Sales Agent Platform API & Developer SDK",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — lock down allow_origins to your frontend domain in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: replace with specific domain before prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket (voice pipeline)
app.include_router(voice_router)

# REST API routes (v1)
app.include_router(tenant_router)
app.include_router(lead_router)
app.include_router(product_router)
app.include_router(campaign_router)
app.include_router(smart_router)
app.include_router(calls_router)
app.include_router(webhooks_router)

# ── Static Frontend & SPA Serving ─────────────────────────────────────────────
root_dir = os.path.dirname(os.path.dirname(__file__))
dist_path = os.path.join(root_dir, "voxsales-app", "dist")
legacy_frontend_path = os.path.join(root_dir, "frontend")

if os.path.exists(dist_path):
    # Mount built assets
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Allow API docs and open routes to bypass
        if full_path.startswith(("docs", "redoc", "openapi.json", "api", "ws")):
            return None
        file_path = os.path.join(dist_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_path, "index.html"))

elif os.path.exists(legacy_frontend_path):
    app.mount("/static", StaticFiles(directory=legacy_frontend_path), name="static")

    @app.get("/styles.css", include_in_schema=False)
    async def serve_css():
        return FileResponse(os.path.join(legacy_frontend_path, "styles.css"))

    @app.get("/app.js", include_in_schema=False)
    async def serve_js():
        return FileResponse(os.path.join(legacy_frontend_path, "app.js"))

    @app.get("/dashboard", include_in_schema=False)
    @app.get("/", include_in_schema=False)
    async def serve_dashboard():
        return FileResponse(os.path.join(legacy_frontend_path, "index.html"))


# Startup/shutdown is handled by the lifespan context manager above.
