import asyncio

from core.mongo_db import get_students_collection, get_teachers_collection


async def main():
    student = await get_students_collection().delete_one({"name": "Hash Fix Student"})
    teacher = await get_teachers_collection().delete_one({"teacher_id": "HFX001"})
    print(f"deleted students {student.deleted_count} teachers {teacher.deleted_count}")


asyncio.run(main())
