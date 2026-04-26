import asyncio
from uuid import uuid4
from sqlalchemy import text
from backend.shared.db.session import get_db_session
from backend.shared.db.models.assessment_session import AssessmentSession

async def create_test_session():
    async for db in get_db_session():
        print("Creating test session...")
        # Get first user
        result = await db.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = result.scalar()
        if not user_id:
            print("No users found.")
            return

        session_id = uuid4()
        new_session = AssessmentSession(
            session_id=str(session_id),
            user_id=user_id,
            status="in_progress",
            submissions={},
            completed_levels=[],
            score=0
        )
        db.add(new_session)
        await db.commit()
        print(f"Created session: {session_id} for user {user_id}")

if __name__ == "__main__":
    asyncio.run(create_test_session())
