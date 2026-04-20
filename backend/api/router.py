from fastapi import APIRouter, Depends

from backend.assessment.router import router as assessment_router
from backend.auth.router import router as auth_router
from backend.auth.dependencies import get_current_user
from backend.evidence.router import router as evidence_router
from backend.profiling.router import router as profiling_router
from backend.rag.router import router as rag_router
from backend.roadmap.router import router as roadmap_router
from backend.session.router import router as session_router
from backend.shared.jobs.router import router as jobs_router
from backend.skill.router import router as skill_router
from backend.validation.router import router as validation_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(assessment_router, prefix="/assessment", tags=["assessment"], dependencies=[Depends(get_current_user)])
api_router.include_router(profiling_router, prefix="/profiling", tags=["profiling"], dependencies=[Depends(get_current_user)])
api_router.include_router(skill_router, prefix="/skills", tags=["skills"], dependencies=[Depends(get_current_user)])
api_router.include_router(roadmap_router, prefix="/roadmaps", tags=["roadmaps"], dependencies=[Depends(get_current_user)])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"], dependencies=[Depends(get_current_user)])
api_router.include_router(session_router, prefix="/sessions", tags=["sessions"], dependencies=[Depends(get_current_user)])
api_router.include_router(evidence_router, prefix="/evidence", tags=["evidence"], dependencies=[Depends(get_current_user)])
api_router.include_router(validation_router, prefix="/validation", tags=["validation"], dependencies=[Depends(get_current_user)])
api_router.include_router(rag_router, prefix="/rag", tags=["rag"], dependencies=[Depends(get_current_user)])
