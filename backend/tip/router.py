from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.shared.db.models import Session
from backend.shared.db.session import get_db_session
from backend.tip.schemas import TipResponse

router = APIRouter()


@router.get("/{session_id}", response_model=TipResponse)
async def get_tip(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> TipResponse:
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        return TipResponse(available=False)

    result = await db_session.execute(
        select(Session)
        .where(Session.id == session_uuid)
        .where(Session.user_id == current_user["user"].id)
    )
    session = result.scalar_one_or_none()

    if not session or session.status != "failed":
        return TipResponse(available=False)

    failure_reason = (session.failure_reason or "protocol_violation").lower()

    if failure_reason == "retry_limit_exceeded":
        return TipResponse(
            available=True,
            severity="critical",
            text="Retry count exceeded. Slow down and checkpoint every protocol step before reattempting.",
            focus_step="2",
        )

    if failure_reason == "metric_threshold":
        return TipResponse(
            available=True,
            severity="moderate",
            text="Your quality threshold dipped. Increase review time and attach one artifact after step 3.",
            focus_step="3",
        )

    return TipResponse(
        available=True,
        severity="moderate",
        text="Protocol adherence broke. Re-run steps 1-4 in strict order without skipping review.",
        focus_step="1",
    )
