
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from backend.shared.db.models import SkillTemplate
from dotenv import load_dotenv

async def check_skills():
    load_dotenv(".env.local")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(SkillTemplate))
        skills = result.scalars().all()
        print(f"Total skills in database: {len(skills)}")
        for skill in skills:
            print(f"- {skill.name} (ID: {skill.skill_id}, Active: {skill.is_active}, Version: {skill.version})")

if __name__ == "__main__":
    asyncio.run(check_skills())
