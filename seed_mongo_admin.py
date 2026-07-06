"""
Seed the MongoDB admin user.
Run once: python seed_mongo_admin.py
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from utils.hash_util import hash_password

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
ADMIN_NAME = os.getenv("ADMIN_NAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

async def seed():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    admins_col = db["admins"]

    existing = await admins_col.find_one({"name_lower": ADMIN_NAME.lower()})
    if existing:
        print(f"Admin '{ADMIN_NAME}' already exists – skipping.")
    else:
        doc = {
            "name": ADMIN_NAME,
            "name_lower": ADMIN_NAME.lower(),
            "password_hash": hash_password(ADMIN_PASSWORD),
            "role": "admin",
        }
        await admins_col.insert_one(doc)
        print(f"✅ Admin '{ADMIN_NAME}' created. Login with password: {ADMIN_PASSWORD}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
