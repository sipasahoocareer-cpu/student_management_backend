"""Test quiz results API endpoint directly"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('d:/studenttt2/backend/.env'))

# Use BACKEND_URL from environment for deployed testing (falls back to localhost)
BASE_URL = os.getenv('BACKEND_URL') or os.getenv('API_BASE_URL') or 'http://localhost:8000'

import httpx

async def test():
    # First get a token by logging in as a teacher
    async with httpx.AsyncClient() as client:
        # Login as teacher
        login_resp = await client.post(
            f'{BASE_URL}/api/mongo/auth/login',
            json={'identifier': 'biswajeet nayak', 'password': 'TEACHER01'}
        )
        print('Login status:', login_resp.status_code)
        if login_resp.status_code != 200:
            print('Login failed:', login_resp.text)
            # Try admin login
            login_resp = await client.post(
                f'{BASE_URL}/api/mongo/auth/login',
                json={'identifier': 'admin', 'password': 'admin123'}
            )
            print('Admin login status:', login_resp.status_code)
            if login_resp.status_code != 200:
                print('Admin login also failed:', login_resp.text)
                return

        data = login_resp.json()
        token = data.get('token')
        print('Role:', data.get('role'))
        print('Token:', token[:40] + '...' if token else None)

        headers = {'Authorization': f'Bearer {token}'}

        # Get quizzes
        quizzes_resp = await client.get(f'{BASE_URL}/api/mongo/quiz', headers=headers)
        print('\nQuizzes status:', quizzes_resp.status_code)
        quizzes_data = quizzes_resp.json()
        print('Quizzes:', quizzes_data)

        if quizzes_data.get('data'):
            quiz_id = quizzes_data['data'][0]['id']
            print(f'\nFetching results for quiz_id={quiz_id!r}')
            results_resp = await client.get(
                f'{BASE_URL}/api/mongo/quiz/{quiz_id}/results',
                headers=headers
            )
            print('Results status:', results_resp.status_code)
            print('Results body:', results_resp.json())

asyncio.run(test())
