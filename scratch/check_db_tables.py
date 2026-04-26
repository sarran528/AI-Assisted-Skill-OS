
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

async def check_tables():
    load_dotenv(".env.local")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Checking tables...")
        result = await session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"Found tables: {', '.join(tables)}")
        
        required_tables = ["users", "skill_templates", "skill_research_objects", "cognitive_profiles", "learning_parameters", "baseline_skill_states"]
        for table in required_tables:
            if table in tables:
                res = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = res.scalar()
                print(f" - {table}: {count} rows")
            else:
                print(f" - {table}: MISSING!")

if __name__ == "__main__":
    asyncio.run(check_tables())
