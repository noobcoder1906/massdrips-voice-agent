"""
backend/main.py

VoxSales Multi-Tenant AI Voice Agent Platform API & Client Dashboard — Phase 7.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from backend.database import connect_to_mongo, close_mongo_connection, db_instance
from backend.ws.voice_ws import router as voice_router
from backend.routes.routes import tenant_router, lead_router, product_router
from backend.routes.campaigns import router as campaign_router
from backend.campaigns.scheduler import scheduler_instance

app = FastAPI(
    title="VoxSales API",
    description="Multi-Tenant AI Voice Sales Agent Platform",
    version="2.0.0",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket (voice pipeline)
app.include_router(voice_router)

# REST API routes
app.include_router(tenant_router)
app.include_router(lead_router)
app.include_router(product_router)
app.include_router(campaign_router)

# Static Frontend Dashboard
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/styles.css", include_in_schema=False)
    async def serve_css():
        return FileResponse(os.path.join(frontend_path, "styles.css"))

    @app.get("/app.js", include_in_schema=False)
    async def serve_js():
        return FileResponse(os.path.join(frontend_path, "app.js"))

    @app.get("/dashboard", include_in_schema=False)
    @app.get("/", include_in_schema=False)
    async def serve_dashboard():
        return FileResponse(os.path.join(frontend_path, "index.html"))


@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    scheduler_instance.start()


@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler_instance.stop()
    await close_mongo_connection()
