"""
Backfill teacher_id onto existing quizzes that only have teacher_name.
Looks up the teacher by name in the teachers collection and copies their email/_id as teacher_id.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('d:/studenttt2/backend/.env'))

from pymongo.asynchronous.mongo_client import AsyncMongoClient

async def fix():
    uri = os.getenv('MONGODB_URI', 'mongodb+srv://rupasahoo2004_db_user:OalamakxI57VyDwy@cluster0.d5kugf8.mongodb.net/')
    db_name = os.getenv('DB_NAME', 'student_management')
    client = AsyncMongoClient(uri)
    db = client[db_name]

    print('=== BACKFILL teacher_id on quizzes ===')
    fixed = 0
    async for quiz in db['quizzes'].find({'teacher_id': {'$exists': False}}):
        teacher_name = quiz.get('teacher_name', '')
        teacher = await db['teachers'].find_one({'name': teacher_name})
        if teacher:
            teacher_id = teacher.get('email') or str(teacher['_id'])
            await db['quizzes'].update_one(
                {'_id': quiz['_id']},
                {'$set': {'teacher_id': teacher_id}}
            )
            print(f'  Fixed quiz {str(quiz["_id"])!r}: teacher_name={teacher_name!r} -> teacher_id={teacher_id!r}')
            fixed += 1
        else:
            print(f'  WARNING: No teacher found for teacher_name={teacher_name!r} in quiz {str(quiz["_id"])}')

    print(f'\nDone. Backfilled {fixed} quiz(es).')
    await client.close()

asyncio.run(fix())
