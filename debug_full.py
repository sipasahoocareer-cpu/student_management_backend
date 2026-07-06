"""
Direct test: simulate teacher clicking Review on a quiz.
Lists all teachers so we can find one that works.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('d:/studenttt2/backend/.env'))

from pymongo.asynchronous.mongo_client import AsyncMongoClient
import httpx

async def test():
    uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'student_management')
    client = AsyncMongoClient(uri)
    db = client[db_name]

    print('=== TEACHERS IN DB ===')
    async for t in db['teachers'].find({}, {'name': 1, 'teacher_id': 1, 'email': 1, '_id': 0}):
        print(f'  name={t.get("name")!r}  teacher_id={t.get("teacher_id")!r}  email={t.get("email")!r}')

    print('\n=== QUIZ SUBMISSIONS RAW ===')
    async for s in db['quiz_submissions'].find({}):
        print(f'  _id={s["_id"]}')
        print(f'  quiz_id={s.get("quiz_id")!r}  (type: {type(s.get("quiz_id")).__name__})')
        print(f'  student_name={s.get("student_name")!r}')
        print()

    print('=== QUIZZES RAW ===')
    async for q in db['quizzes'].find({}):
        print(f'  _id={q["_id"]}  (type: {type(q["_id"]).__name__})')
        print(f'  str(_id)={str(q["_id"])!r}')
        print()

    await client.close()

    # Now test the API with admin token (known working)
    async with httpx.AsyncClient() as http:
        login = await http.post(
            'https://student-management-backend-jqc5.onrender.com/api/mongo/auth/login',
            json={'identifier': 'admin', 'password': 'admin123'}
        )
        token = login.json().get('token')
        headers = {'Authorization': f'Bearer {token}'}

        quizzes = await http.get('hhttps://student-management-backend-jqc5.onrender.com/api/mongo/quiz', headers=headers)
        quiz_data = quizzes.json().get('data', [])
        print(f'=== QUIZZES FROM API ({len(quiz_data)} total) ===')
        for q in quiz_data:
            quiz_id = q['id']
            print(f'  quiz_id={quiz_id!r}  title={q["title"]!r}')
            results = await http.get(
                f'https://student-management-backend-jqc5.onrender.com/api/mongo/quiz/{quiz_id}/results',
                headers=headers
            )
            rd = results.json()
            print(f'  results status={results.status_code}  count={len(rd.get("results", []))}')
            for sub in rd.get('results', []):
                print(f'    -> student={sub.get("student_name")!r}  answers={sub.get("answers")}')

asyncio.run(test())
