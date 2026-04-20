from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.assessment.schemas import LearningParameters
from backend.roadmap.generator import generate_roadmap, verify_roadmap_integrity
from backend.roadmap.schemas import GeneratedRoadmap
from backend.shared.audit import log_audit_event
from backend.shared.db.models import (
    CognitiveProfile,
    LearningParameter,
    Roadmap,
    SkillResearchObjectModel,
    SkillTemplate,
)
from backend.shared.db.repositories.roadmap_repository import RoadmapRepository
from backend.shared.db.repositories.skill_research_repository import SkillResearchRepository
from backend.shared.errors import BusinessError, SystemError
from backend.skill.intelligence import SkillResearchObject


def _learning_params_from_model(model: LearningParameter) -> LearningParameters:
    payload: dict[str, float | int] = {}
    for field in LearningParameters.model_fields:
        value = getattr(model, field)
        if isinstance(value, int):
            payload[field] = value
        else:
            payload[field] = float(value)
    return LearningParameters.model_validate(payload)


async def _fetch_latest_learning_parameters(
    db: AsyncSession,
    user_id: UUID,
    skill_id: str,
) -> LearningParameter | None:
    stmt = (
        select(LearningParameter)
        .join(CognitiveProfile, CognitiveProfile.id == LearningParameter.profile_id)
        .where(CognitiveProfile.user_id == user_id)
        .where(LearningParameter.skill_id == skill_id)
        .order_by(desc(CognitiveProfile.version), desc(LearningParameter.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


def _fetch_latest_learning_parameters_sync(
    db: Session,
    user_id: UUID,
    skill_id: str,
) -> LearningParameter | None:
    stmt = (
        select(LearningParameter)
        .join(CognitiveProfile, CognitiveProfile.id == LearningParameter.profile_id)
        .where(CognitiveProfile.user_id == user_id)
        .where(LearningParameter.skill_id == skill_id)
        .order_by(desc(CognitiveProfile.version), desc(LearningParameter.created_at))
        .limit(1)
    )
    result = db.execute(stmt)
    return result.scalars().first()


async def create_roadmap(db: AsyncSession, user_id: UUID, skill_id: str) -> GeneratedRoadmap:
    existing = await RoadmapRepository.get_active(db, user_id, skill_id)
    if existing is not None:
        return GeneratedRoadmap.model_validate(existing.structure)

    research_model = await SkillResearchRepository.get_latest(db, user_id, skill_id)
    if research_model is None:
        raise BusinessError("research_required", "Skill research is required before roadmap generation")

    research = SkillResearchObject.model_validate(research_model.payload)

    template_stmt = (
        select(SkillTemplate)
        .where(SkillTemplate.skill_id == skill_id)
        .where(SkillTemplate.is_active == True)
        .order_by(SkillTemplate.version.desc())
        .limit(1)
    )
    template_result = await db.execute(template_stmt)
    template = template_result.scalars().first()
    if template is None:
        raise BusinessError("skill_not_found", f"No active template found for skill '{skill_id}'")

    parameters_model = await _fetch_latest_learning_parameters(db, user_id, skill_id)
    if parameters_model is None:
        raise BusinessError("parameters_required", "Learning parameters are required")
    parameters = _learning_params_from_model(parameters_model)

    generated = generate_roadmap(research, template, parameters, parameters_model.id)
    if not verify_roadmap_integrity(generated):
        raise SystemError("Generated roadmap failed integrity verification")

    await RoadmapRepository.create(db, generated, user_id, parameters_model.id)
    await log_audit_event(
        db,
        user_id=str(user_id),
        action="roadmap.generated",
        entity_type="roadmap",
        entity_id=None,
        ip_address=None,
        metadata={"skill_id": skill_id, "fingerprint": generated.fingerprint},
    )
    return generated


def sync_create_roadmap(db: Session, user_id: UUID, skill_id: str) -> dict:
    existing = (
        db.execute(
            select(Roadmap)
            .where(Roadmap.user_id == user_id)
            .where(Roadmap.skill_id == skill_id)
            .where(Roadmap.status == "active")
            .order_by(Roadmap.created_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    if existing is not None:
        return {"id": str(existing.id), "fingerprint": existing.fingerprint}

    research_model = (
        db.execute(
            select(SkillResearchObjectModel)
            .where(SkillResearchObjectModel.user_id == user_id)
            .where(SkillResearchObjectModel.skill_id == skill_id)
            .order_by(SkillResearchObjectModel.created_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    if research_model is None:
        raise BusinessError("research_required", "Skill research is required before roadmap generation")

    template = (
        db.execute(
            select(SkillTemplate)
            .where(SkillTemplate.skill_id == skill_id)
            .where(SkillTemplate.is_active == True)
            .order_by(SkillTemplate.version.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    if template is None:
        raise BusinessError("skill_not_found", f"No active template found for skill '{skill_id}'")

    parameters_model = _fetch_latest_learning_parameters_sync(db, user_id, skill_id)
    if parameters_model is None:
        raise BusinessError("parameters_required", "Learning parameters are required")

    generated = generate_roadmap(
        SkillResearchObject.model_validate(research_model.payload),
        template,
        _learning_params_from_model(parameters_model),
        parameters_model.id,
    )
    if not verify_roadmap_integrity(generated):
        raise SystemError("Generated roadmap failed integrity verification")

    roadmap_model = Roadmap(
        user_id=user_id,
        skill_id=generated.skill_id,
        template_version=generated.template_version,
        profile_version=generated.profile_version,
        parameters_id=parameters_model.id,
        structure=generated.model_dump(mode="json"),
        fingerprint=generated.fingerprint,
        status="active",
    )
    db.add(roadmap_model)
    db.commit()
    db.refresh(roadmap_model)
    return {"id": str(roadmap_model.id), "fingerprint": roadmap_model.fingerprint}
