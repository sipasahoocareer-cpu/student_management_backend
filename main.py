import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from utils.hash_util import hash_password

# ── Legacy SQLAlchemy imports (kept for backward compatibility) ────────────────
try:
    from core.database import init_db
    _legacy_db = True
except Exception:
    _legacy_db = False

# ── Legacy routers ────────────────────────────────────────────────────────────
try:
    from router.api import router as api_router
    from router.admin_router import router as admin_router
    _legacy_routers = True
except Exception:
    _legacy_routers = False

# ── New MongoDB routers ───────────────────────────────────────────────────────
from router.mongo_student_router import router as mongo_student_router
from router.mongo_teacher_router import router as mongo_teacher_router
from router.mongo_academic_router import router as mongo_academic_router
from router.mongo_quiz_router import router as mongo_quiz_router
from router.contact_router import router as contact_router
from core.mongo_db import get_admins_collection

app = FastAPI(title="Student Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",

        "https://studentmanagement123212.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback

    traceback.print_exc()
    origin = request.headers.get("origin") or request.headers.get("Origin") or "*"
    headers = {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
    }
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"}, headers=headers)


@app.on_event("startup")
async def on_startup():
    # Legacy SQLite init
    if _legacy_db:
        try:
            init_db()
        except Exception as e:
            print(f"[WARN] Legacy DB init skipped: {e}")

    # Seed MongoDB admin
    await _seed_mongo_admin()


async def _seed_mongo_admin():
    """Create the default admin in MongoDB if not present."""
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
    admin_name = os.getenv("ADMIN_NAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    try:
        col = get_admins_collection()
        existing = await col.find_one({"name_lower": admin_name.lower()})
        if not existing:
            await col.insert_one({
                "name": admin_name,
                "name_lower": admin_name.lower(),
                "password_hash": hash_password(admin_password),
                "role": "admin",
            })
            print(f"[INFO] Admin '{admin_name}' seeded into MongoDB.")
        else:
            print(f"[INFO] Admin '{admin_name}' already exists in MongoDB.")
    except Exception as e:
        print(f"[WARN] MongoDB admin seed failed: {e}")


# ── Register legacy routers ───────────────────────────────────────────────────
if _legacy_routers:
    app.include_router(api_router, prefix="/api")
    app.include_router(admin_router, tags=["admin"])

# ── Register new MongoDB routers ──────────────────────────────────────────────
app.include_router(mongo_student_router, prefix="/api/mongo", tags=["mongo-students"])
app.include_router(mongo_teacher_router, prefix="/api/mongo", tags=["mongo-teachers"])
app.include_router(mongo_academic_router, prefix="/api/mongo", tags=["mongo-academic"])
app.include_router(mongo_quiz_router, prefix="/api/mongo", tags=["mongo-quiz"])
app.include_router(contact_router, prefix="/api/mongo", tags=["contact"])


@app.get("/")
def root():
    return {
        "message": "Student Management API",
        "endpoints": {
            "student_login": "/api/mongo/auth/login",
            "students_crud": "/api/mongo/students",
            "contact_us": "/api/mongo/contact",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
