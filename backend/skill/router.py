"""
API routes for skill template management.
"""

import logging
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
    SkillDiscoverRequest,
    SkillDiscoverResponse,
    SkillResearchComposeRequest,
    SkillResearchComposeResponse,
    SkillAnalysisRequest,
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
from backend.shared.config import settings
from backend.assessment.profile_vector import ProfileVector
from backend.skill.intelligence import SkillAnalysisResponse, SkillResearchObject
from backend.skill.template_pipeline import to_skill_id
from sqlalchemy import select
from backend.shared.queue.provider import queue_roadmap_generation, queue_skill_discovery, queue_skill_research_compose

router = APIRouter()
logger = logging.getLogger(__name__)


def _flatten_template_constants(structure: dict, complexity_score: float) -> dict:
    strict = structure.get("structured_template", {}) if isinstance(structure, dict) else {}
    phases_obj = strict.get("phases", {}) if isinstance(strict, dict) else {}
    if not phases_obj:
        phases_obj = structure.get("phases", {}) if isinstance(structure, dict) else {}

    phase_names = list(phases_obj.keys())
    techniques: list[str] = []
    checkpoints: list[str] = []
    prerequisites: list[str] = []

    for phase_name, phase_data in phases_obj.items():
        if not isinstance(phase_data, dict):
            continue
        prerequisites.extend([str(c) for c in phase_data.get("competencies", [])])
        for technique in phase_data.get("techniques", []):
            if isinstance(technique, dict):
                t_name = str(technique.get("name", technique.get("id", "technique")))
                techniques.append(t_name)
                for cp in technique.get("checkpoints", []):
                    if isinstance(cp, dict):
                        checkpoints.append(str(cp.get("competency_target", cp.get("target_metric", "checkpoint"))))
            else:
                techniques.append(str(technique))
        for cp in phase_data.get("checkpoints", []):
            checkpoints.append(str(cp))

    # Deterministic constant from discovered structure and complexity.
    estimated_total_hours = max(24, int((len(phase_names) * 18) + (len(techniques) * 4) + (complexity_score * 60)))
    return {
        "phases": phase_names,
        "techniques": techniques,
        "checkpoints": checkpoints,
        "prerequisites": sorted(set(prerequisites)),
        "estimated_total_hours": estimated_total_hours,
    }


def _difficulty_modifier(payload: SkillResearchComposeRequest, profile: ProfileVector) -> float:
    modifier = 1.0
    exp_weight = {"beginner": 0.2, "intermediate": 0.0, "advanced": -0.15}
    goal_weight = {"hobby": -0.05, "professional": 0.1, "exam": 0.15}
    modifier += exp_weight.get(payload.experience_level, 0.0)
    modifier += goal_weight.get(payload.target_goal, 0.0)
    if payload.hours_per_week < 4:
        modifier += 0.25
    elif payload.hours_per_week >= 12:
        modifier -= 0.1
    if not payload.has_required_tools:
        modifier += 0.2
    modifier += (0.5 - float(profile.time_constraint)) * 0.1
    return max(0.5, min(2.0, modifier))


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


@router.post("/discover", response_model=SkillDiscoverResponse, status_code=status.HTTP_201_CREATED)
async def discover_skill_from_internet(
    payload: SkillDiscoverRequest,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Discover/generate a skill template from internet sources for any user."""
    _ = db_session
    try:
        normalized_skill_id = to_skill_id(payload.skill_name)
        _, job_id = await queue_skill_discovery(
            skill_name=payload.skill_name,
            domain=payload.domain,
            complexity_score=payload.complexity_score,
            requested_by_user_id=str(current_user.user.id),
        )
        return SkillDiscoverResponse(
            skill_id=normalized_skill_id,
            name=payload.skill_name,
            domain=payload.domain,
            complexity_score=float(payload.complexity_score),
            version=0,
            created=False,
            status="queued_inngest",
            job_id=job_id,
        )
    except BusinessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.args[0],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover skill: {str(e)}",
        )


@router.post("/analyze", response_model=SkillAnalysisResponse)
async def analyze_skill_preliminary(
    payload: SkillAnalysisRequest,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Execute Stages 1-4: Preliminary research and analysis to generate user questions."""
    try:
        service = SkillIntelligenceService(db_session)
        analysis_response = await service.analyze_skill_preliminary(payload.skill_name)
        return analysis_response
    except Exception as e:
        logger.error(f"Preliminary analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze skill: {str(e)}",
        )


@router.post("/research/compose", response_model=SkillResearchComposeResponse, status_code=status.HTTP_201_CREATED)
async def compose_skill_research(
    payload: SkillResearchComposeRequest,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Merge internet research + user answers + profile into SkillResearchObject."""
    try:
        normalized_skill_id = to_skill_id(payload.skill_id)

        profile_record = await db_session.scalar(
            select(CognitiveProfile)
            .where(CognitiveProfile.user_id == current_user.user.id)
            .order_by(CognitiveProfile.created_at.desc())
        )
        if not profile_record:
            raise BusinessError(
                code="no_profile_found",
                message="User profile not found. Complete assessment first.",
            )

        profile = ProfileVector(
            cognitive_capacity=float(profile_record.cognitive_capacity),
            attention_stability=float(profile_record.attention_stability),
            learning_tolerance=float(profile_record.learning_tolerance),
            motor_baseline=float(profile_record.motor_baseline),
            stress_resilience=float(profile_record.stress_resilience),
            time_constraint=float(profile_record.time_constraint),
        )

        constants = {
            "phases": [],
            "techniques": [],
            "checkpoints": [],
            "prerequisites": [],
            "estimated_total_hours": 60,
        }
        skill_service = SkillTemplateService(db_session)
        try:
            template = await skill_service.get_skill(normalized_skill_id)
            constants = _flatten_template_constants(template.structure or {}, float(template.complexity_score))
        except BusinessError:
            logger.info(
                "Template not yet available during compose; proceeding with default constants",
                extra={"skill_id": normalized_skill_id, "user_id": str(current_user.user.id)},
            )
        difficulty_modifier = _difficulty_modifier(payload, profile)

        # Ensure baseline exists from user answers if prior probes were skipped.
        grounding_repo = GroundingRepository(db_session)
        baseline = await grounding_repo.get_latest_baseline(current_user.user.id, normalized_skill_id)
        if baseline is None:
            recognition_map = {"beginner": 0.25, "intermediate": 0.55, "advanced": 0.8}
            declarative_map = {"beginner": 0.2, "intermediate": 0.5, "advanced": 0.75}
            confidence_base = {"beginner": 0.3, "intermediate": 0.6, "advanced": 0.8}
            confidence_score = confidence_base[payload.experience_level] + (0.05 if payload.has_required_tools else -0.05)
            confidence_score = max(0.0, min(1.0, confidence_score))
            perceived_level = (recognition_map[payload.experience_level] + declarative_map[payload.experience_level] + confidence_score) / 3.0
            confidence_bias = max(-1.0, min(1.0, perceived_level - profile.cognitive_capacity))

            await grounding_repo.create_baseline(
                user_id=current_user.user.id,
                skill_id=normalized_skill_id,
                exposure_score=recognition_map[payload.experience_level],
                declarative_score=declarative_map[payload.experience_level],
                confidence_score=confidence_score,
                perceived_level=perceived_level,
                actual_level=profile.cognitive_capacity,
                confidence_bias=confidence_bias,
                raw_responses=payload.model_dump(),
            )

        queue_payload = {
            "user_id": str(current_user.user.id),
            "skill_id": normalized_skill_id,
            "user_goal": payload.target_goal,
            "difficulty_modifier": difficulty_modifier,
            "user_answers": payload.model_dump(),
            "template_constants": constants,
            "profile": profile.model_dump(),
            "search_provider": settings.search_provider,
            "serp_aspects": [
                "skill_definition_and_scope",
                "foundational_subskills",
                "tooling_and_prerequisites",
                "learning_path_milestones",
                "portfolio_project_ideas",
                "market_demand_and_roles",
                "common_beginner_mistakes",
            ],
        }

        queue_provider, research_job_id = await queue_skill_research_compose(queue_payload)

        try:
            _, job_id = await queue_roadmap_generation(
                user_id=str(current_user.user.id),
                skill_id=normalized_skill_id,
            )
            return SkillResearchComposeResponse(
                skill_id=normalized_skill_id,
                status=f"queued_{queue_provider}",
                roadmap_job_id=job_id,
                research_job_id=research_job_id,
            )
        except Exception as e:
            logger.error(f"Failed to queue roadmap task: {e}")
            return SkillResearchComposeResponse(
                skill_id=normalized_skill_id,
                status="persisted_but_not_queued",
                roadmap_job_id="none",
                research_job_id=research_job_id,
            )
    except BusinessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if e.code != "skill_not_found" else status.HTTP_404_NOT_FOUND,
            detail=e.args[0],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compose skill research: {str(e)}",
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
            normalized_skill_id = to_skill_id(payload.skill_id)
            normalized_confidence = max(0.0, min(1.0, payload.confidence_bias / 5.0))
            perceived_level = (payload.recognition_score + payload.declarative_score + normalized_confidence) / 3.0
            confidence_bias_value = max(-1.0, min(1.0, perceived_level - profile.cognitive_capacity))

            repo = GroundingRepository(db_session)
            await repo.create_baseline(
                user_id=current_user.user.id,
                skill_id=normalized_skill_id,
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
                skill_id=normalized_skill_id,
                exposure_score=payload.recognition_score,
                declarative_knowledge=payload.declarative_score,
                confidence_bias=payload.confidence_bias,
                adjusted_repetition_intensity=adjusted_repetition_intensity,
            )

        # Submit grounding with full probe responses
        service = GroundingService(db_session)
        normalized_skill_id = to_skill_id(payload.skill_id)
        response = await service.submit_grounding(
            user_id=current_user.user.id,
            skill_id=normalized_skill_id,
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
    baseline = await repo.get_latest_baseline(current_user.user.id, to_skill_id(skill_id))
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
            skill_id=to_skill_id(skill_id),
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
