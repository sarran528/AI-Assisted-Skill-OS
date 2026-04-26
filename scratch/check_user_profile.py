
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from backend.shared.db.models import CognitiveProfile, User, AssessmentSession
from dotenv import load_dotenv

async def check_user_profile():
    load_dotenv(".env.local")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User))
        user = result.scalars().first()
        if not user:
            print("No user found")
            return
        
        print(f"Checking profile for user: {user.email} ({user.id})")
        
        result = await session.execute(
            select(CognitiveProfile).where(CognitiveProfile.user_id == user.id)
        )
        profiles = result.scalars().all()
        print(f"Total profiles: {len(profiles)}")
        for p in profiles:
            print(f"- Profile ID: {p.id}, Version: {p.version}, Created: {p.created_at}")

        result = await session.execute(
            select(AssessmentSession).where(AssessmentSession.user_id == str(user.id))
        )
        sessions = result.scalars().all()
        print(f"Total assessment sessions: {len(sessions)}")
        for s in sessions:
            print(f"- Session ID: {s.session_id}, Status: {s.status}, Completed Levels: {s.completed_levels}")

if __name__ == "__main__":
    asyncio.run(check_user_profile())
