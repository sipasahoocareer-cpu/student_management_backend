import asyncio
from core.mongo_db import get_admins_collection
from utils.hash_util import verify_password

async def main():
    col = get_admins_collection()
    doc = await col.find_one({'name_lower':'admin'})
    print('DOC:', doc)
    if doc:
        print('password_hash:', bool(doc.get('password_hash')))
        print('password_plain:', doc.get('password'))
        print('verify with admin123 ->', verify_password('admin123', doc.get('password_hash')) if doc.get('password_hash') else doc.get('password') == 'admin123')

asyncio.run(main())
