"""
API routes for skill template management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import AuthContext, get_current_user
from backend.shared.db.session import get_db_session
from backend.shared.errors import BusinessError, SystemError
from backend.skill.schemas import (
    SkillTemplateCreate,
    SkillTemplateUpdate,
    SkillTemplateResponse,
    SkillListResponse,
    SkillTemplateBuildRequest,
    SkillTemplateBuildResponse,
)
from backend.skill.grounding_schemas import (
    GroundingProbeResponses,
    GroundingProbeSubmit,
    BaselineStateResponse,
)
from backend.skill.service import SkillTemplateService
from backend.skill.grounding_service import GroundingService
from backend.shared.db.repositories.grounding_repository import GroundingRepository
from backend.skill.intelligence_service import SkillIntelligenceService
from backend.shared.db.models import CognitiveProfile
from backend.assessment.profile_vector import ProfileVector
from backend.skill.intelligence import SkillResearchObject
from sqlalchemy import select

router = APIRouter()


@router.get("", response_model=list[SkillListResponse])
async def list_skills(
    current_user: AuthContext = Depends(get_current_user),
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


@router.get("/list", response_model=list[SkillListResponse])
async def list_skills_alias(
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    return await list_skills(current_user=current_user, db_session=db_session)


@router.get("/{skill_id}", response_model=SkillTemplateResponse)
async def get_skill(
    skill_id: str,
    current_user: AuthContext = Depends(get_current_user),
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
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new skill template (admin only)."""
    # Check admin status
    if current_user.user.status != "admin":
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


@router.post("/generate-template", response_model=SkillTemplateBuildResponse, status_code=status.HTTP_201_CREATED)
async def generate_skill_template(
    payload: SkillTemplateBuildRequest,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Generate and persist a template using structured retrieval pipeline (admin only)."""
    if current_user.user.status != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can generate skill templates",
        )

    try:
        service = SkillTemplateService(db_session)
        template, generated_version, created = await service.build_template_from_skill_name(
            skill_name=payload.skill_name,
            domain=payload.domain,
            complexity_score=payload.complexity_score,
        )
        return SkillTemplateBuildResponse(
            skill_id=template.skill_id,
            version=generated_version,
            created=created,
        )
    except BusinessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.args[0],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate skill template: {str(e)}",
        )


@router.put("/{skill_id}", response_model=SkillTemplateResponse)
async def update_skill(
    skill_id: str,
    payload: SkillTemplateUpdate,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update an existing skill template (admin only)."""
    if current_user.user.status != "admin":
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


@router.post("/baseline", response_model=BaselineStateResponse)
async def submit_grounding(
    payload: GroundingProbeResponses | GroundingProbeSubmit,
    request: Request,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Submit grounding probe responses for a skill."""
    try:
        # Fetch user's latest cognitive profile
        result = await db_session.execute(
            select(CognitiveProfile)
            .where(CognitiveProfile.user_id == current_user.user.id)
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
        
        ip_address = request.client.host if request.client else "127.0.0.1"

        if isinstance(payload, GroundingProbeSubmit):
            normalized_confidence = max(0.0, min(1.0, payload.confidence_bias / 5.0))
            perceived_level = (payload.recognition_score + payload.declarative_score + normalized_confidence) / 3.0
            confidence_bias_value = max(-1.0, min(1.0, perceived_level - profile.cognitive_capacity))

            repo = GroundingRepository(db_session)
            await repo.create_baseline(
                user_id=current_user.user.id,
                skill_id=payload.skill_id,
                exposure_score=payload.recognition_score,
                declarative_score=payload.declarative_score,
                confidence_score=normalized_confidence,
                perceived_level=perceived_level,
                actual_level=profile.cognitive_capacity,
                confidence_bias=confidence_bias_value,
                raw_responses={"recognition_score": payload.recognition_score, "declarative_score": payload.declarative_score},
            )

            adjusted_repetition_intensity = max(
                0.0,
                min(1.0, 1.0 - ((payload.recognition_score + payload.declarative_score) / 2.0)),
            )

            return BaselineStateResponse(
                skill_id=payload.skill_id,
                exposure_score=payload.recognition_score,
                declarative_knowledge=payload.declarative_score,
                confidence_bias=payload.confidence_bias,
                adjusted_repetition_intensity=adjusted_repetition_intensity,
            )

        # Submit grounding with full probe responses
        service = GroundingService(db_session)
        response = await service.submit_grounding(
            user_id=current_user.user.id,
            skill_id=payload.skill_id,
            responses=payload,
            profile=profile,
            ip_address=ip_address,
        )

        adjusted_repetition_intensity = max(
            0.0,
            min(1.0, 1.0 - ((response.exposure_score + response.declarative_score) / 2.0)),
        )

        return BaselineStateResponse(
            skill_id=response.skill_id,
            exposure_score=float(response.exposure_score),
            declarative_knowledge=float(response.declarative_score),
            confidence_bias=float(response.confidence_bias),
            adjusted_repetition_intensity=adjusted_repetition_intensity,
        )
        
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


@router.get("/{skill_id}/baseline", response_model=BaselineStateResponse)
async def get_baseline(
    skill_id: str,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> BaselineStateResponse:
    repo = GroundingRepository(db_session)
    baseline = await repo.get_latest_baseline(current_user.user.id, skill_id)
    if baseline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="baseline_not_found")

    adjusted_repetition_intensity = max(
        0.0,
        min(1.0, 1.0 - ((float(baseline.exposure_score) + float(baseline.declarative_score)) / 2.0)),
    )

    return BaselineStateResponse(
        skill_id=baseline.skill_id,
        exposure_score=float(baseline.exposure_score),
        declarative_knowledge=float(baseline.declarative_score),
        confidence_bias=float(baseline.confidence_bias),
        adjusted_repetition_intensity=adjusted_repetition_intensity,
    )


@router.post("/research", response_model=SkillResearchObject)
async def generate_skill_research(
    skill_id: str,
    request: Request,
    current_user: AuthContext = Depends(get_current_user),
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
            .where(CognitiveProfile.user_id == current_user.user.id)
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
            user_id=current_user.user.id,
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
    except SystemError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service failed. Please try again later.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate skill research: {str(e)}",
        )
