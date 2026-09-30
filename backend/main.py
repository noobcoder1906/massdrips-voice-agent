from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import connect_to_mongo, close_mongo_connection, db_instance
from backend.ws.voice_ws import router as voice_router
from backend.routes.routes import tenant_router, lead_router, product_router
import uvicorn

app = FastAPI(
    title="VoxSales API",
    description="Multi-Tenant AI Voice Sales Agent Platform",
    version="2.0.0",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── WebSocket (voice pipeline) ─────────────────────────────────────────────────
app.include_router(voice_router)

# ── REST API routes ────────────────────────────────────────────────────────────
app.include_router(tenant_router)
app.include_router(lead_router)
app.include_router(product_router)


@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()


@app.get("/", tags=["Health"])
async def root():
    try:
        await db_instance.client.admin.command('ping')
        db_status = "MongoDB connected"
    except Exception as e:
        db_status = f"MongoDB disconnected: {str(e)}"
    return {"status": "VoxSales API is running", "version": "2.0.0", "db": db_status}


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
