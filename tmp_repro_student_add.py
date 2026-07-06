import traceback
from fastapi.testclient import TestClient
from main import app
from router.mongo_auth import create_token

client = TestClient(app)
token = create_token({'sub':'admin','role':'admin','name':'admin','email':''})
try:
    resp = client.post('/api/mongo/students', json={'name':'Test Student','password':'1234','class_name':'1'}, headers={'Authorization': f'Bearer {token}'})
    print('status', resp.status_code)
    print(resp.text)
except Exception:
    traceback.print_exc()
