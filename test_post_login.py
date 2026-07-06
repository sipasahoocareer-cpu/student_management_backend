import httpx

r = httpx.post('https://student-management-backend-jqc5.onrender.com/api/mongo/auth/login', json={'identifier':'admin','password':'admin123'}, timeout=20.0)
print('STATUS', r.status_code)
print('HEADERS')
for k,v in r.headers.items():
    print(k+':', v)
print('BODY')
print(r.text)
