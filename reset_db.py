from core.database import init_db, SessionLocal, Base, engine, DB_URL
from core.crud import create_user
import os

# Delete and recreate database only for SQLite local backups
if DB_URL.startswith('sqlite'):
    db_path = DB_URL.replace('sqlite:///', '', 1)
    if os.path.exists(db_path):
        try:
            Base.metadata.drop_all(bind=engine)
            print("Tables dropped")
        except Exception as e:
            print(f"Error dropping tables: {e}")
    else:
        print("SQLite database file not found; skipping drop.")
else:
    try:
        Base.metadata.drop_all(bind=engine)
        print("Tables dropped")
    except Exception as e:
        print(f"Error dropping tables on PostgreSQL: {e}")

# Initialize database
init_db()
print("Database initialized")

# Create test users
db = SessionLocal()
try:
    # Admin
    admin = create_user(db, 'Sarah Mitchell', 'admin@school.com', 'admin123', role='admin')
    print(f"✓ Admin created: {admin.email}")
    
    # Teacher
    teacher = create_user(db, 'Dr. James Wilson', 'teacher@school.com', 'teacher123', role='teacher', subject='Computer Science')
    print(f"✓ Teacher created: {teacher.email}")
    
    # Student
    student = create_user(db, 'Alex Rivera', 'student@school.com', 'student123', role='student', rollNumber='STU-2024-0847', batch='2024-A', subject='Engineering')
    print(f"✓ Student created: {student.email}")
    
    print("\nAll test users created successfully!")
    
finally:
    db.close()
