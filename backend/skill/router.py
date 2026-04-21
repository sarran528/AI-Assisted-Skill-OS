"""
API routes for skill template management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.shared.db.session import get_db_session
from backend.shared.errors import BusinessError, SystemError
from backend.skill.schemas import (
    SkillTemplateCreate,
    SkillTemplateUpdate,
    SkillTemplateResponse,
    SkillListResponse,
)
from backend.skill.grounding_schemas import (
    GroundingProbeResponses,
    BaselineSkillStateResponse,
)
from backend.skill.service import SkillTemplateService
from backend.skill.grounding_service import GroundingService
from backend.skill.intelligence_service import SkillIntelligenceService
from backend.shared.db.models import CognitiveProfile
from backend.assessment.profile_vector import ProfileVector
from backend.skill.intelligence import SkillResearchObject
from sqlalchemy import select

router = APIRouter()


@router.get("", response_model=list[SkillListResponse])
async def list_skills(
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List all active skill templates."""
    try:
        service = SkillTemplateService(db_session)
        templates = await service.list_skills()
        return [
            SkillListResponse(
                id=t.id,
                skill_id=t.skill_id,
                name=t.name,
                domain=t.domain,
                complexity_score=float(t.complexity_score),
                version=t.version,
            )
            for t in templates
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skills: {str(e)}",
        )


@router.get("/{skill_id}", response_model=SkillTemplateResponse)
async def get_skill(
    skill_id: str,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific skill template by skill_id."""
    try:
        service = SkillTemplateService(db_session)
        template = await service.get_skill(skill_id)
        return SkillTemplateResponse(
            id=template.id,
            skill_id=template.skill_id,
            version=template.version,
            name=template.name,
            domain=template.domain,
            complexity_score=float(template.complexity_score),
            structure=template.structure,
            is_active=template.is_active,
            created_at=template.created_at,
        )
    except BusinessError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.args[0],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill: {str(e)}",
        )


@router.post("", response_model=SkillTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: SkillTemplateCreate,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new skill template (admin only)."""
    # Check admin status
    if current_user.get("status") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create skill templates",
        )

    try:
        service = SkillTemplateService(db_session)
        template = await service.create_skill_template(payload)
        return SkillTemplateResponse(
            id=template.id,
            skill_id=template.skill_id,
            version=template.version,
            name=template.name,
            domain=template.domain,
            complexity_score=float(template.complexity_score),
            structure=template.structure,
            is_active=template.is_active,
            created_at=template.created_at,
        )
    except BusinessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.args[0],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill: {str(e)}",
        )


@router.put("/{skill_id}", response_model=SkillTemplateResponse)
async def update_skill(
    skill_id: str,
    payload: SkillTemplateUpdate,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update an existing skill template (admin only)."""
    if current_user.get("status") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update skill templates",
        )

    try:
        service = SkillTemplateService(db_session)
        template = await service.update_skill_template(skill_id, payload)
        return SkillTemplateResponse(
            id=template.id,
            skill_id=template.skill_id,
            version=template.version,
            name=template.name,
            domain=template.domain,
            complexity_score=float(template.complexity_score),
            structure=template.structure,
            is_active=template.is_active,
            created_at=template.created_at,
        )
    except BusinessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if e.code != "skill_not_found" else status.HTTP_404_NOT_FOUND,
            detail=e.args[0],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill: {str(e)}",
        )


@router.post("/baseline", response_model=BaselineSkillStateResponse)
async def submit_grounding(
    payload: GroundingProbeResponses,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Submit grounding probe responses for a skill."""
    try:
        # Fetch user's latest cognitive profile
        result = await db_session.execute(
            select(CognitiveProfile)
            .where(CognitiveProfile.user_id == current_user["user"].id)
            .order_by(CognitiveProfile.created_at.desc())
        )
        profile_record = result.scalar_one_or_none()
        
        if not profile_record:
            raise BusinessError(
                code="no_profile_found",
                message="User profile not found. Complete assessment first.",
            )
        
        # Convert to ProfileVector
        profile = ProfileVector(
            cognitive_capacity=float(profile_record.cognitive_capacity),
            attention_stability=float(profile_record.attention_stability),
            learning_tolerance=float(profile_record.learning_tolerance),
            motor_baseline=float(profile_record.motor_baseline),
            stress_resilience=float(profile_record.stress_resilience),
            time_constraint=float(profile_record.time_constraint),
        )
        
        # Submit grounding
        service = GroundingService(db_session)
        ip_address = request.client.host if request.client else "127.0.0.1"
        
        response = await service.submit_grounding(
            user_id=current_user["user"].id,
            skill_id=payload.skill_id,
            responses=payload,
            profile=profile,
            ip_address=ip_address,
        )
        
        return response
        
    except BusinessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if e.code != "skill_not_found" else status.HTTP_404_NOT_FOUND,
            detail=e.args[0],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit grounding: {str(e)}",
        )


@router.post("/research", response_model=SkillResearchObject)
async def generate_skill_research(
    skill_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Generate skill intelligence research object.
    
    Orchestrates four LLM calls to produce complete intelligence package.
    Requires prior grounding probes to have been submitted.
    """
    try:
        # Fetch user's latest cognitive profile
        result = await db_session.execute(
            select(CognitiveProfile)
            .where(CognitiveProfile.user_id == current_user["user"].id)
            .order_by(CognitiveProfile.created_at.desc())
        )
        profile_record = result.scalar_one_or_none()
        
        if not profile_record:
            raise BusinessError(
                code="no_profile_found",
                message="User profile not found. Complete assessment first.",
            )
        
        # Convert to ProfileVector
        profile = ProfileVector(
            cognitive_capacity=float(profile_record.cognitive_capacity),
            attention_stability=float(profile_record.attention_stability),
            learning_tolerance=float(profile_record.learning_tolerance),
            motor_baseline=float(profile_record.motor_baseline),
            stress_resilience=float(profile_record.stress_resilience),
            time_constraint=float(profile_record.time_constraint),
        )
        
        # Generate skill research
        service = SkillIntelligenceService(db_session)
        ip_address = request.client.host if request.client else "127.0.0.1"
        
        research_object = await service.generate_skill_research(
            user_id=current_user["user"].id,
            skill_id=skill_id,
            profile=profile,
            ip_address=ip_address,
        )
        
        return research_object.model_dump(mode="json")
        
    except BusinessError as e:
        status_code = {
            "skill_not_found": status.HTTP_404_NOT_FOUND,
            "grounding_required": status.HTTP_400_BAD_REQUEST,
            "no_profile_found": status.HTTP_400_BAD_REQUEST,
        }.get(e.code, status.HTTP_400_BAD_REQUEST)
        
        raise HTTPException(
            status_code=status_code,
            detail=e.args[0],
        )
    except SystemError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service failed. Please try again later.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate skill research: {str(e)}",
        )
