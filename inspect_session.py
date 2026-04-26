import asyncio
import json
from sqlalchemy import select
from backend.shared.db.session import get_db_session
from backend.shared.db.models import AssessmentSession

async def inspect_session():
    async for db in get_db_session():
        stmt = select(AssessmentSession).order_by(AssessmentSession.created_at.desc()).limit(1)
        session = await db.scalar(stmt)
        if session:
            print(f"Session ID: {session.session_id}")
            print(f"Status: {session.status}")
            print(f"Completed Levels: {session.completed_levels}")
            print("Submissions JSON:")
            print(json.dumps(session.submissions, indent=2))
        else:
            print("No sessions found")

if __name__ == "__main__":
    asyncio.run(inspect_session())
