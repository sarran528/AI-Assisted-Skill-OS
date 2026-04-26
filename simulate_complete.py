import asyncio
from uuid import UUID
from sqlalchemy import select
from backend.shared.db.session import get_db_session
from backend.shared.db.models import AssessmentSession
from backend.assessment.service import process_assessment_levels
from backend.assessment.schemas import AssessmentSubmission

async def simulate_complete():
    session_id = "769cbb27-51a4-4d4c-90e2-519ad3a75bb4"
    user_id = "965ccff5-e409-4d33-8185-c3cf5b6d3705"
    
    async for db in get_db_session():
        try:
            print(f"Fetching session {session_id} for user {user_id}")
            stmt = select(AssessmentSession).where(
                AssessmentSession.session_id == str(session_id),
                AssessmentSession.user_id == str(user_id)
            )
            session = await db.scalar(stmt)
            if not session:
                print("Session not found")
                return

            print(f"Session found. Submissions: {len(session.submissions or {})}")
            
            # If empty, let's see why
            submissions_payload = list((session.submissions or {}).values())
            print(f"Payload list: {submissions_payload}")
            
            # This is where it might crash if payload is weird
            submissions = [AssessmentSubmission.model_validate(item) for item in submissions_payload]
            print(f"Validated {len(submissions)} submissions")
            
            # This is the main call
            if len(submissions) < 6:
                print("Incomplete assessment (expected 6 levels)")
                # return # We'll try anyway if there's any data
            
            if not submissions:
                print("No submissions to process")
                return

            profile = await process_assessment_levels(
                db_session=db,
                user_id=UUID(user_id),
                submissions=submissions,
                session_id=UUID(session_id)
            )
            print("Profile computed successfully!")
            print(f"Profile ID: {profile.id}")
            
        except Exception as e:
            print(f"CRASH DETECTED: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simulate_complete())
