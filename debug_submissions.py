"""Debug quiz submissions in MongoDB"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('d:/studenttt2/backend/.env'))

from pymongo.asynchronous.mongo_client import AsyncMongoClient

async def check():
    uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'student_management')
    client = AsyncMongoClient(uri)
    db = client[db_name]

    print('=== ALL QUIZ SUBMISSIONS ===')
    count = 0
    async for s in db['quiz_submissions'].find({}):
        count += 1
        print(f'  quiz_id={s.get("quiz_id")!r}')
        print(f'  student={s.get("student_name")!r}  student_id={s.get("student_id")!r}')
        print(f'  answers={s.get("answers")}')
        print(f'  submitted_at={s.get("submitted_at")}')
        print()
    if count == 0:
        print('  (no submissions found in quiz_submissions collection)')

    print('=== ALL QUIZZES ===')
    async for q in db['quizzes'].find({}):
        from bson import ObjectId
        qid = str(q['_id'])
        print(f'  _id={qid!r}  title={q.get("title")!r}  class_name={q.get("class_name")!r}')

    await client.close()

asyncio.run(check())
