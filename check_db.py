import asyncio
from sqlalchemy import text
from backend.shared.db.session import get_db_session

async def check_schema():
    async for db in get_db_session():
        result = await db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'assessment_sessions'"))
        columns = result.fetchall()
        print("Columns in assessment_sessions:")
        for col in columns:
            print(f" - {col[0]}: {col[1]}")

if __name__ == "__main__":
    asyncio.run(check_schema())
