import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('d:/studenttt2/backend/.env'))

from pymongo.asynchronous.mongo_client import AsyncMongoClient

async def check():
    uri = os.getenv('MONGODB_URI', 'mongodb+srv://rupasahoo2004_db_user:OalamakxI57VyDwy@cluster0.d5kugf8.mongodb.net/')
    db_name = os.getenv('DB_NAME', 'student_management')
    client = AsyncMongoClient(uri)
    db = client[db_name]

    print('=== ALL QUIZZES ===')
    count = 0
    async for q in db['quizzes'].find({}):
        count += 1
        cn = q.get('class_name')
        print(f'  title={q.get("title")} | class_name={cn!r} | type={type(cn).__name__}')
    if count == 0:
        print('  (no quizzes found)')

    print()
    print('=== STUDENTS class_name values ===')
    async for s in db['students'].find({}, {'name': 1, 'class_name': 1, '_id': 0}):
        cn = s.get('class_name')
        print(f'  name={s.get("name")} | class_name={cn!r} | type={type(cn).__name__}')

    await client.close()

asyncio.run(check())
