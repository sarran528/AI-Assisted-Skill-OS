import asyncio
import json
from sqlalchemy import select
from backend.shared.db.session import get_db_session
from backend.shared.db.models import AssessmentSession

async def check_user_sessions():
    user_id = "965ccff5-e409-4d33-8185-c3cf5b6d3705"
    async for db in get_db_session():
        stmt = select(AssessmentSession).where(AssessmentSession.user_id == user_id).order_by(AssessmentSession.created_at.desc())
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        print(f"Found {len(sessions)} sessions for user {user_id}")
        for s in sessions:
            print(f"ID: {s.session_id} | Status: {s.status} | Levels: {len(s.submissions or {})} | Created: {s.created_at}")

if __name__ == "__main__":
    asyncio.run(check_user_sessions())
