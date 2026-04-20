from __future__ import annotations

import hashlib
import math
from collections import OrderedDict
from datetime import datetime, timezone

import canonicaljson

from backend.assessment.schemas import LearningParameters
from backend.roadmap.schemas import (
    GeneratedRoadmap,
    RoadmapCheckpoint,
    RoadmapPhase,
    RoadmapTechnique,
)
from backend.skill.intelligence import SkillResearchObject
from backend.shared.db.models.skill_template import SkillTemplate

DEFAULT_PROTOCOL_STEPS = [
    "Set up materials",
    "Execute technique",
    "Review output",
    "Record observations",
]

ARTIFACT_KEYWORDS = ("produce", "draw", "create", "record", "write")
NUMERIC_KEYWORDS = ("accuracy", "score", "percentage", "within")


def _build_phase_techniques(
    phase_data: dict,
    params: LearningParameters,
    technique_defs: dict,
) -> list[RoadmapTechnique]:
    available_techniques = list(phase_data.get("techniques", []))
    sorted_techniques = sorted(available_techniques)
    selected_count = max(1, math.floor(float(params.technique_density) * len(sorted_techniques)))

    techniques: list[RoadmapTechnique] = []
    session_count = max(1, round(float(params.repetition_intensity) * 3))

    for technique_name in sorted_techniques[:selected_count]:
        definition = technique_defs.get(technique_name, {}) if isinstance(technique_defs, dict) else {}
        protocol_steps = definition.get("protocol_steps") or DEFAULT_PROTOCOL_STEPS

        techniques.append(
            RoadmapTechnique(
                technique_id=technique_name,
                name=technique_name,
                session_count=session_count,
                protocol_steps=list(protocol_steps),
            )
        )

    return techniques


def _checkpoint_evidence_type(checkpoint_text: str) -> str:
    lowered = checkpoint_text.lower()
    if any(keyword in lowered for keyword in ARTIFACT_KEYWORDS):
        return "artifact"
    if any(keyword in lowered for keyword in NUMERIC_KEYWORDS):
        return "numeric"
    return "behavioral_log"


def generate_roadmap(
    research: SkillResearchObject,
    template: SkillTemplate,
    params: LearningParameters,
    parameters_id,
) -> GeneratedRoadmap:
    structure = template.structure or {}
    phases_source = structure.get("phases", {})
    technique_defs = structure.get("technique_definitions", {})

    phases: "OrderedDict[str, RoadmapPhase]" = OrderedDict()

    for phase_slug, phase_data in phases_source.items():
        competencies = list(phase_data.get("competencies", []))
        if research.feasibility.risk_level == "high" and len(competencies) > 3:
            competencies = competencies[:3]

        checkpoints_source = list(phase_data.get("checkpoints", []))
        checkpoints = [
            RoadmapCheckpoint(
                checkpoint_id=f"{phase_slug}_cp_{idx + 1}",
                description=checkpoint,
                evidence_type=_checkpoint_evidence_type(checkpoint),
                threshold=float(params.checkpoint_rigidity),
                pass_criteria=checkpoint,
            )
            for idx, checkpoint in enumerate(checkpoints_source)
        ]

        estimated_weeks = int(research.time_model.hours_per_phase.get(phase_slug, 2))
        phases[phase_slug] = RoadmapPhase(
            phase_slug=phase_slug,
            competencies=competencies,
            techniques=_build_phase_techniques(phase_data, params, technique_defs),
            checkpoints=checkpoints,
            estimated_weeks=estimated_weeks,
            status="locked",
        )

    phase_keys = list(phases.keys())
    if phase_keys:
        phases[phase_keys[0]].status = "active"

    total_estimated_weeks = sum(phase.estimated_weeks for phase in phases.values())
    generated_at = datetime.now(timezone.utc)

    base_payload = {
        "skill_id": research.skill_id,
        "user_id": str(research.user_id),
        "profile_version": research.profile_version,
        "template_version": int(template.version),
        "parameters_id": str(parameters_id),
        "phases": {
            key: phase.model_dump(mode="json")
            for key, phase in phases.items()
        },
        "total_estimated_weeks": total_estimated_weeks,
    }
    fingerprint = hashlib.sha256(canonicaljson.encode_canonical_json(base_payload)).hexdigest()

    return GeneratedRoadmap(
        skill_id=research.skill_id,
        user_id=research.user_id,
        profile_version=research.profile_version,
        template_version=int(template.version),
        parameters_id=parameters_id,
        phases=dict(phases),
        total_estimated_weeks=total_estimated_weeks,
        fingerprint=fingerprint,
        generated_at=generated_at,
    )


def verify_roadmap_integrity(roadmap: GeneratedRoadmap) -> bool:
    serialized = canonicaljson.encode_canonical_json(
        roadmap.model_dump(mode="json", exclude={"fingerprint", "generated_at"})
    )
    expected = hashlib.sha256(serialized).hexdigest()
    return roadmap.fingerprint == expected
