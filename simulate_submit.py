import asyncio
from uuid import uuid4
from backend.shared.db.session import get_db_session
from backend.shared.db.models import AssessmentSession
from sqlalchemy import select

async def simulate_submit():
    # Use the session ID from the user's log
    session_id = "769cbb27-51a4-4d4c-90e2-519ad3a75bb4"
    user_id = "965ccff5-e409-4d33-8185-c3cf5b6d3705"
    
    async for db in get_db_session():
        try:
            print(f"Attempting to submit level 1 for session {session_id}")
            stmt = select(AssessmentSession).where(
                AssessmentSession.session_id == str(session_id),
                AssessmentSession.user_id == str(user_id)
            )
            session = await db.scalar(stmt)
            if not session:
                print("Session not found")
                return

            print("Session found. Updating submissions...")
            # Simulate the router logic
            submissions = dict(session.submissions or {})
            submissions["1"] = {
                "level": 1,
                "metrics": {"accuracy": 1.0, "expected_time": 1.0, "latency_stability": 0, "decay_inverse": 1, "dropout": 0, "retry": 0, "recovery": 1},
                "time_constraint": {"available_hours_per_week": 10, "preferred_session_length": 30},
                "score": 100
            }
            session.submissions = submissions
            session.completed_levels = [1]
            
            # This is where the crash happened before
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(session, "submissions")
            flag_modified(session, "completed_levels")
            
            await db.commit()
            print("Submit successful!")
            
        except Exception as e:
            print(f"CRASH DETECTED: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simulate_submit())
