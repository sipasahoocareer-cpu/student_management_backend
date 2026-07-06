import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    try:
        client = AsyncIOMotorClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000)
        await client.admin.command('ping')
        print('MongoDB: CONNECTED')
        db = client['student_management']

        admins = await db['admins'].find().to_list(10)
        print('Admins count:', len(admins))
        for a in admins:
            print('  Admin name:', a.get('name'), '| name_lower:', a.get('name_lower'), '| role:', a.get('role'))

        students = await db['students'].find().to_list(10)
        print('Students count:', len(students))
        for s in students:
            print('  Student name:', s.get('name'), '| reg:', s.get('registration_number'))

    except Exception as e:
        print('MongoDB ERROR:', e)

asyncio.run(check())
