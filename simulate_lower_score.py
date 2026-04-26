import asyncio
from backend.shared.db.session import get_db_session
from backend.shared.db.models import AssessmentSession
from sqlalchemy import select

async def simulate_lower_score():
    session_id = "769cbb27-51a4-4d4c-90e2-519ad3a75bb4"
    user_id = "965ccff5-e409-4d33-8185-c3cf5b6d3705"
    
    async for db in get_db_session():
        try:
            print(f"Fetching session {session_id}")
            stmt = select(AssessmentSession).where(
                AssessmentSession.session_id == str(session_id),
                AssessmentSession.user_id == str(user_id)
            )
            session = await db.scalar(stmt)
            
            level_key = "1"
            existing_submission = session.submissions.get(level_key)
            existing_score = int(existing_submission.get("score", 0))
            print(f"Existing score for level 1: {existing_score}")
            
            # New lower score
            new_score = existing_score - 50
            print(f"New lower score: {new_score}")
            
            submissions = dict(session.submissions or {})
            new_submission = {
                "level": 1,
                "metrics": {"accuracy": 0.5, "expected_time": 10.0, "latency_stability": 0, "decay_inverse": 1, "dropout": 0, "retry": 0, "recovery": 1},
                "time_constraint": {"available_hours_per_week": 10, "preferred_session_length": 30},
                "score": new_score
            }
            
            # Use the user's logic
            if existing_submission is None or int(new_score) >= existing_score:
                submissions[level_key] = new_submission
                print("Updating submission")
            else:
                print("Score lower, NOT updating submission")
            
            total_score = sum(s.get("score", 0) for s in submissions.values())
            session.score = total_score
            
            session.submissions = submissions
            session.updated_at = asyncio.get_event_loop().time() # Fake time for test
            
            await db.commit()
            print("Submit successful (even if not updated)!")
            
        except Exception as e:
            print(f"CRASH DETECTED: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simulate_lower_score())
