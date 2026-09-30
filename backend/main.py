from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import connect_to_mongo, close_mongo_connection
from backend.ws.voice_ws import router as voice_router
import uvicorn

app = FastAPI(
    title="VoxSales API",
    description="Multi-Tenant AI Voice Sales Agent Platform",
    version="1.0.0",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the WebSocket endpoints
app.include_router(voice_router)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"status": "VoxSales API is running", "db": "MongoDB connected"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
