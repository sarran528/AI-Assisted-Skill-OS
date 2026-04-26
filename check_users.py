import asyncio
from sqlalchemy import text
from backend.shared.db.session import get_db_session

async def check_users():
    async for db in get_db_session():
        result = await db.execute(text("SELECT id, email FROM users"))
        users = result.fetchall()
        print(f"Total users: {len(users)}")
        for user in users:
            print(f" - {user[0]}: {user[1]}")

if __name__ == "__main__":
    asyncio.run(check_users())
