import os
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Use pymongo for a quick connectivity check before creating the async client
from pymongo import MongoClient as PyMongoClient

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "student_management")

_client: AsyncIOMotorClient = None
_client_loop = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Return a cached AsyncIOMotorClient.

    Attempts a quick synchronous ping against the configured URI. If the
    initial connection fails (common with remote Atlas TLS issues on dev
    machines), fall back to a local MongoDB at mongodb://localhost:27017.
    """
    global _client, _client_loop
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _client is not None and _client_loop is not None:
        if _client_loop.is_closed() or (current_loop is not None and _client_loop is not current_loop):
            _client.close()
            _client = None
            _client_loop = None

    if _client is None:
        is_srv_uri = urlparse(MONGODB_URI).scheme == "mongodb+srv"
        # First try the configured URI quickly
        try:
            test_client = PyMongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            test_client.admin.command("ping")
            test_client.close()
            client_kwargs = {"serverSelectionTimeoutMS": 30000}
            if is_srv_uri:
                client_kwargs.update({
                    "tls": True,
                    "tlsAllowInvalidCertificates": True,
                })
            _client = AsyncIOMotorClient(MONGODB_URI, **client_kwargs)
            _client_loop = current_loop
        except Exception as e:
            print(f"[WARN] Primary MongoDB URI failed: {e}. Falling back to localhost.")
            try:
                _client = AsyncIOMotorClient(
                    "mongodb://localhost:27017",
                    serverSelectionTimeoutMS=30000,
                )
                _client_loop = current_loop
            except Exception as e2:
                print(f"[ERROR] Fallback MongoDB connection failed: {e2}")
                raise
    return _client


def get_database():
    client = get_mongo_client()
    return client[DB_NAME]


# Collection shortcuts
def get_students_collection():
    return get_database()["students"]


def get_teachers_collection():
    return get_database()["teachers"]


def get_queries_collection():
    return get_database()["contact_queries"]


def get_admins_collection():
    return get_database()["admins"]


async def close_mongo_connection():
    global _client, _client_loop
    if _client:
        _client.close()
        _client = None
        _client_loop = None
