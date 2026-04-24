from __future__ import annotations

import hashlib
import math
import re
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Callable

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
SKILL_OVERRIDES: dict[str, dict[str, Callable[[float], float]]] = {
    "drawing": {"difficulty_slope": lambda p: p + 0.15 * 0.4},
    "coding": {
        "abstraction_level": lambda p: min(p + 0.1, 1.0),
        "technique_density": lambda p: max(p - 0.1, 0.0),
    },
    "music": {
        "repetition_intensity": lambda p: min(p + 0.15, 1.0),
        "checkpoint_rigidity": lambda p: min(p + 0.1, 1.0),
    },
    "language": {"phase_pacing": lambda p: p},
    "high_complexity": {"technique_density": lambda p: min(p, 0.7)},
    "low_tolerance": {"repetition_intensity": lambda p: max(p, 0.6)},
}


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def _apply_modifiers(
    params: LearningParameters,
    confidence_bias: float,
    technique_density_adjustment: float,
    repetition_boost: float,
) -> LearningParameters:
    """Apply skill and confidence adjustments to learning parameters."""
    adjusted_technique_density = _clamp_unit(
        float(params.technique_density) + float(technique_density_adjustment)
    )
    adjusted_repetition = _clamp_unit(
        float(params.repetition_intensity)
        + float(repetition_boost)
        + float(confidence_bias) * 0.15
    )
    adjusted_hint_threshold = _clamp_unit(
        float(params.hint_activation_threshold) - float(confidence_bias) * 0.1
    )

    return params.model_copy(
        update={
            "technique_density": adjusted_technique_density,
            "repetition_intensity": adjusted_repetition,
            "hint_activation_threshold": adjusted_hint_threshold,
        }
    )


def _build_phase_techniques(
    phase_data: dict,
    params: LearningParameters,
    technique_defs: dict,
) -> list[RoadmapTechnique]:
    available_techniques = list(phase_data.get("techniques", []))
    selected_count = max(1, math.floor(float(params.technique_density) * len(available_techniques)))
    selected_count = min(selected_count, max(1, int(params.concurrent_technique_limit)))
    sorted_techniques = sorted(available_techniques, key=lambda item: item.get("name", item.get("id", "")) if isinstance(item, dict) else str(item))

    techniques: list[RoadmapTechnique] = []
    session_count = max(1, round(float(params.repetition_intensity) * 3))

    for technique_entry in sorted_techniques[:selected_count]:
        if isinstance(technique_entry, dict):
            technique_name = str(technique_entry.get("name", technique_entry.get("id", "technique")))
            protocol_steps = list(technique_entry.get("protocol_steps") or DEFAULT_PROTOCOL_STEPS)
        else:
            technique_name = str(technique_entry)
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


def _extract_numeric_threshold(threshold: str, fallback: float) -> float:
    matches = re.findall(r"\d+(?:\.\d+)?", threshold)
    if not matches:
        return fallback
    numeric = float(matches[0])
    if "%" in threshold:
        return max(0.0, min(1.0, numeric / 100.0))
    return numeric


def _apply_skill_overrides(params: LearningParameters, template: SkillTemplate) -> LearningParameters:
    updated = params.model_dump()
    domain_key = (template.domain or "").lower()
    complexity_key = "high_complexity" if float(template.complexity_score) >= 0.7 else ""
    tolerance_key = "low_tolerance" if float(params.error_tolerance_threshold) < 0.4 else ""
    for key in (domain_key, complexity_key, tolerance_key):
        if not key:
            continue
        overrides = SKILL_OVERRIDES.get(key, {})
        for field, transform in overrides.items():
            if field in updated:
                updated[field] = _clamp_unit(float(transform(float(updated[field]))))
    return LearningParameters.model_validate(updated)


def generate_roadmap(
    research: SkillResearchObject,
    template: SkillTemplate,
    params: LearningParameters,
    parameters_id,
) -> GeneratedRoadmap:
    structure = template.structure or {}
    phases_source = structure.get("phases", {})
    technique_defs = structure.get("technique_definitions", {})

    adjusted_params = _apply_modifiers(
        params=params,
        confidence_bias=float(research.confidence_bias),
        technique_density_adjustment=float(research.skill_modifiers.technique_density_adjustment),
        repetition_boost=float(research.skill_modifiers.repetition_boost),
    )
    adjusted_params = _apply_skill_overrides(adjusted_params, template)

    strict_structure = structure.get("structured_template", {})
    strict_phases = strict_structure.get("phases", {}) if isinstance(strict_structure, dict) else {}
    use_strict = isinstance(strict_phases, dict) and len(strict_phases) > 0
    if use_strict:
        phases_source = strict_phases

    phases: "OrderedDict[str, RoadmapPhase]" = OrderedDict()

    for phase_slug, phase_data in phases_source.items():
        competencies = list(phase_data.get("competencies", []))
        if research.feasibility.risk_level == "high" and len(competencies) > 3:
            competencies = competencies[:3]

        checkpoints_source = list(phase_data.get("checkpoints", []))
        if use_strict:
            checkpoints_source = [
                checkpoint
                for technique in phase_data.get("techniques", [])
                if isinstance(technique, dict)
                for checkpoint in technique.get("checkpoints", [])
                if isinstance(checkpoint, dict)
            ]
        checkpoints = [
            RoadmapCheckpoint(
                checkpoint_id=checkpoint.get("id", f"{phase_slug}_cp_{idx + 1}") if isinstance(checkpoint, dict) else f"{phase_slug}_cp_{idx + 1}",
                description=checkpoint.get("competency_target", checkpoint.get("target_metric", "checkpoint")) if isinstance(checkpoint, dict) else checkpoint,
                evidence_type=(
                    checkpoint.get("validation_method", "behavioral_log")
                    if isinstance(checkpoint, dict) and checkpoint.get("validation_method") in {"numeric", "artifact", "behavioral_log"}
                    else _checkpoint_evidence_type(str(checkpoint))
                ),
                threshold=(
                    _extract_numeric_threshold(str(checkpoint.get("threshold", "")), float(adjusted_params.checkpoint_rigidity))
                    if isinstance(checkpoint, dict)
                    else float(adjusted_params.checkpoint_rigidity)
                ),
                pass_criteria=checkpoint.get("threshold", str(checkpoint)) if isinstance(checkpoint, dict) else checkpoint,
            )
            for idx, checkpoint in enumerate(checkpoints_source)
        ]

        estimated_weeks = int(research.time_model.hours_per_phase.get(phase_slug, 2))
        phases[phase_slug] = RoadmapPhase(
            phase_slug=phase_slug,
            competencies=competencies,
            techniques=_build_phase_techniques(phase_data, adjusted_params, technique_defs),
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
