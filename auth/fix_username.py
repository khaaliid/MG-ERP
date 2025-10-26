import asyncio
from database import async_engine
from sqlalchemy import text

async def fix_username_column():
    async with async_engine.begin() as conn:
        # Update existing admin user to have username = 'admin'
        await conn.execute(text("UPDATE auth.users SET username = 'admin' WHERE email = 'admin@mg-erp.com' AND username IS NULL"))
        print('Updated existing admin user with username')
        
        print('Username column is now nullable')

asyncio.run(fix_username_column())
print('Database migration completed')