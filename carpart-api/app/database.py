import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "carpart")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "products")

client: AsyncIOMotorClient | None = None

def get_client() -> AsyncIOMotorClient:
    global client
    if client is None:
        client = AsyncIOMotorClient(MONGO_URL)
    return client

def get_collection():
    return get_client()[MONGO_DB][MONGO_COLLECTION]

def get_db():
    return get_client()[MONGO_DB]
