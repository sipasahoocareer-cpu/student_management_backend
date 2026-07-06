import os
import httpx

BASE_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000').rstrip('/')

r = httpx.post(f'{BASE_URL}/api/mongo/auth/login', json={'identifier':'admin','password':'admin123'}, timeout=20.0)
print('STATUS', r.status_code)
print('HEADERS')
for k,v in r.headers.items():
    print(k+':', v)
print('BODY')
print(r.text)
