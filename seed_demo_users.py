"""
Seed demo users into the database.
Run: python seed_demo_users.py
"""
import sys
from core.database import init_db, SessionLocal
from core.crud import create_user, get_user_by_email, get_password_hash

DEMO_USERS = [
    {
        "name": "Sarah Mitchell",
        "email": "admin@school.com",
        "password": "admin123",
        "role": "admin",
    },
    {
        "name": "Dr. James Wilson",
        "email": "teacher@school.com",
        "password": "teacher123",
        "role": "teacher",
    },
    {
        "name": "Alex Rivera",
        "email": "student@school.com",
        "password": "student123",
        "role": "student",
    },
]


def main():
    print("Initialising database…")
    init_db()

    db = SessionLocal()
    try:
        for demo in DEMO_USERS:
            existing = get_user_by_email(db, demo["email"])
            if existing:
                # Update password & role in case they changed
                existing.password = get_password_hash(demo["password"])
                existing.role = demo["role"]
                db.commit()
                print(f"  [updated] {demo['email']} (role={demo['role']})")
            else:
                create_user(
                    db,
                    demo["name"],
                    demo["email"],
                    demo["password"],
                    role=demo["role"],
                )
                print(f"  [created] {demo['email']} (role={demo['role']})")

        print("\nDemo users seeded successfully!")
        print("\nCredentials:")
        for demo in DEMO_USERS:
            print(f"  {demo['role'].capitalize():10s} → {demo['email']}  /  {demo['password']}")

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
