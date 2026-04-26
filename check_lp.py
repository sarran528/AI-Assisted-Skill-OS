import asyncio
from sqlalchemy import text
from backend.shared.db.session import get_db_session

async def check_lp_columns():
    async for db in get_db_session():
        result = await db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'learning_parameters'"))
        columns = [r[0] for r in result.fetchall()]
        print("Columns in learning_parameters:")
        for col in sorted(columns):
            print(f" - {col}")

if __name__ == "__main__":
    asyncio.run(check_lp_columns())
