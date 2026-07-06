"""
Fix existing quiz class_name values in MongoDB.
Changes 'CLASS 9' -> '9', 'CLASS 10' -> '10', 'PGDCA' stays 'PGDCA', etc.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('d:/studenttt2/backend/.env'))

from pymongo.asynchronous.mongo_client import AsyncMongoClient

async def fix():
    uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'student_management')
    client = AsyncMongoClient(uri)
    db = client[db_name]
    col = db['quizzes']

    print('=== FIXING QUIZ class_name VALUES ===')
    fixed = 0
    async for quiz in col.find({}):
        old_cn = quiz.get('class_name', '')
        # Normalize: strip "CLASS " prefix (case-insensitive)
        new_cn = old_cn.strip()
        if new_cn.upper().startswith('CLASS '):
            new_cn = new_cn[6:].strip()  # Remove "CLASS " prefix
        new_cn = new_cn.upper()

        if new_cn != old_cn:
            await col.update_one({'_id': quiz['_id']}, {'$set': {'class_name': new_cn}})
            print(f'  Fixed: {old_cn!r} -> {new_cn!r}  (title={quiz.get("title")})')
            fixed += 1
        else:
            print(f'  OK:    {old_cn!r}  (title={quiz.get("title")})')

    print(f'\nDone. Fixed {fixed} quiz(es).')
    await client.close()

asyncio.run(fix())
