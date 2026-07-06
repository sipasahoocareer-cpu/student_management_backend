import asyncio
from core.mongo_db import get_mongo_client

async def main():
    try:
        client = get_mongo_client()
        print('client created')
        db = client['student_management']
        col = db['admins']
        doc = await col.find_one({})
        print('doc:', doc)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
