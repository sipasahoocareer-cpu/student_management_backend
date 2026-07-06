from fastapi.testclient import TestClient
from main import app

# run in-process so exceptions propagate
client = TestClient(app, raise_server_exceptions=True)

try:
    r = client.post('/api/mongo/auth/login', json={'identifier':'admin','password':'admin123'})
    print('STATUS', r.status_code)
    print('HEADERS', r.headers)
    print('BODY', r.text)
except Exception as e:
    import traceback

    print('EXCEPTION RAISED:')
    traceback.print_exc()
