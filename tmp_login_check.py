import asyncio
import json
from router.mongo_student_router import student_login
from pydantic import BaseModel
from fastapi import HTTPException

class Payload(BaseModel):
    identifier: str
    password: str

async def main():
    try:
        result = await student_login(Payload(identifier='admin', password='admin123'))
        print(json.dumps(result, default=str))
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
