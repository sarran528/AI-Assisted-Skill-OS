import asyncio
from sqlalchemy import text
from backend.shared.db.session import get_db_session

async def run_migration():
    async for db in get_db_session():
        print("Running migrations...")
        try:
            await db.execute(text("ALTER TABLE assessment_sessions ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 0"))
            await db.execute(text("ALTER TABLE assessment_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"))
            await db.commit()
            print("Successfully updated assessment_sessions table.")
        except Exception as e:
            print(f"Error updating assessment_sessions: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(run_migration())
