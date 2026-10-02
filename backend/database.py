import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

import certifi

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "voxsales")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    print(f"Connecting to MongoDB at {MONGO_URI}...")
    kwargs = {}
    if "mongodb+srv" in MONGO_URI or "tls=true" in MONGO_URI.lower():
        kwargs["tlsCAFile"] = certifi.where()
    db_instance.client = AsyncIOMotorClient(MONGO_URI, **kwargs)
    db_instance.db = db_instance.client[DB_NAME]
    print("Connected to MongoDB successfully!")

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        print("MongoDB connection closed.")

def get_db():
    """Dependency to get the database instance."""
    return db_instance.db
