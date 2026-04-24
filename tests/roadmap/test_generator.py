from datetime import datetime
from uuid import uuid4

from backend.assessment.schemas import LearningParameters
from backend.roadmap.generator import generate_roadmap, verify_roadmap_integrity
from backend.roadmap.schemas import GeneratedRoadmap
from backend.shared.db.models.skill_template import SkillTemplate
from backend.shared.llm.schemas import FeasibilityResult, RiskZoneResult, SkillModifierResult, TimeModelResult
from backend.skill.intelligence import SkillResearchObject


def _params(technique_density: float = 0.5, repetition_intensity: float = 0.5) -> LearningParameters:
    return LearningParameters(
        difficulty_slope=0.5,
        phase_pacing=0.5,
        entry_phase_offset=0.5,
        repetition_intensity=repetition_intensity,
        session_duration=0.5,
        micro_session_enabled=0,
        fatigue_threshold=0.5,
        break_frequency=0.5,
        technique_density=technique_density,
        concurrent_technique_limit=2,
        abstraction_level=0.5,
        instruction_granularity=0.5,
        checkpoint_frequency=0.5,
        checkpoint_rigidity=0.85,
        error_tolerance_threshold=0.8,
        retry_limit=2,
        drill_depth=0.5,
        variation_intensity=0.5,
        stress_exposure_rate=0.5,
        simulation_complexity=0.5,
        feedback_detail_level=0.5,
        correction_delay_window=0.5,
        hint_activation_threshold=0.5,
        precision_requirement=0.5,
        speed_requirement=0.5,
        coordination_complexity=0.5,
        adaptation_sensitivity=0.5,
        risk_zone_trigger_level=0.5,
        regression_policy_strength=0.5,
        phase_transition_sensitivity=0.5,
        complexity_escalation_trigger=0.5,
        plateau_detection_threshold=0.5,
        stability_requirement_before_advance=0.5,
    )


def _template() -> SkillTemplate:
    return SkillTemplate(
        id=uuid4(),
        skill_id="drawing",
        version=1,
        name="Drawing",
        domain="art",
        complexity_score=0.5,
        structure={
            "phases": {
                "phase_1": {
                    "competencies": ["c1", "c2", "c3", "c4", "c5"],
                    "techniques": ["blend", "stroke", "shade", "line"],
                    "checkpoints": [
                        "produce 5 shapes",
                        "achieve 90% accuracy",
                        "complete all protocol steps",
                    ],
                },
                "phase_2": {
                    "competencies": ["c6"],
                    "techniques": ["perspective"],
                    "checkpoints": ["create final sketch"],
                },
            },
            "technique_definitions": {
                "blend": {"protocol_steps": ["s1", "s2", "s3"]},
                "line": {"protocol_steps": ["l1", "l2"]},
            },
        },
        is_active=True,
        created_at=datetime.utcnow(),
    )


def _template_with_structured() -> SkillTemplate:
    return SkillTemplate(
        id=uuid4(),
        skill_id="drawing",
        version=1,
        name="Drawing",
        domain="drawing",
        complexity_score=0.5,
        structure={
            "phases": {
                "phase_1": {
                    "competencies": ["legacy"],
                    "techniques": ["legacy-technique"],
                    "checkpoints": ["legacy checkpoint"],
                }
            },
            "structured_template": {
                "skill_id": "drawing",
                "phases": {
                    "phase_1": {
                        "competencies": ["line control", "shape accuracy"],
                        "techniques": [
                            {
                                "id": "tech_a",
                                "name": "Contour drill",
                                "protocol_steps": ["observe", "draw", "review"],
                                "checkpoints": [
                                    {
                                        "id": "cp_percent",
                                        "competency_target": "line control",
                                        "target_metric": "accuracy %",
                                        "threshold": ">= 85%",
                                        "validation_method": "numeric",
                                        "failure_condition": "< 85%",
                                    },
                                    {
                                        "id": "cp_artifact",
                                        "competency_target": "shape accuracy",
                                        "target_metric": "artifact quality",
                                        "threshold": ">= 1 accepted artifact",
                                        "validation_method": "artifact",
                                        "failure_condition": "no accepted artifact",
                                    },
                                ],
                            }
                        ],
                    }
                },
            },
        },
        is_active=True,
        created_at=datetime.utcnow(),
    )


def _research(risk_level: str = "low") -> SkillResearchObject:
    return SkillResearchObject(
        skill_id="drawing",
        user_id=uuid4(),
        profile_version=1,
        feasibility=FeasibilityResult(feasible=True, risk_level=risk_level, blockers=[], confidence=0.9),
        risk_zones=RiskZoneResult(risks=[]),
        time_model=TimeModelResult(estimated_weeks=8, hours_per_phase={"phase_1": 3}, confidence=0.8),
        skill_modifiers=SkillModifierResult(
            technique_density_adjustment=0.0,
            repetition_boost=0.0,
            notes="",
        ),
        confidence_bias=0.0,
        generated_at=datetime.utcnow(),
        is_feasible=True,
        estimated_weeks=8,
        overall_risk=risk_level,
    )


def test_determinism_and_integrity():
    research = _research()
    template = _template()
    params = _params()
    pid = uuid4()

    roadmap1 = generate_roadmap(research, template, params, pid)
    roadmap2 = generate_roadmap(research, template, params, pid)

    roadmap1_json = roadmap1.model_dump(mode="json")
    roadmap2_json = roadmap2.model_dump(mode="json")
    roadmap1_json["generated_at"] = roadmap2_json["generated_at"]

    assert roadmap1_json == roadmap2_json
    assert verify_roadmap_integrity(roadmap1)


def test_determinism_100_runs_same_fingerprint():
    research = _research()
    template = _template()
    params = _params()
    pid = uuid4()

    fingerprints = {generate_roadmap(research, template, params, pid).fingerprint for _ in range(100)}
    assert len(fingerprints) == 1


def test_fingerprint_mutation_fails_verify():
    roadmap = generate_roadmap(_research(), _template(), _params(), uuid4())
    payload = roadmap.model_dump(mode="json")
    payload["phases"]["phase_1"]["competencies"][0] = "tampered"
    tampered = GeneratedRoadmap.model_validate(payload)
    assert verify_roadmap_integrity(tampered) is False


def test_feasibility_filter_high_risk_caps_competencies():
    roadmap = generate_roadmap(_research(risk_level="high"), _template(), _params(), uuid4())
    assert len(roadmap.phases["phase_1"].competencies) == 3


def test_technique_selection_and_minimum_one():
    roadmap_half = generate_roadmap(_research(), _template(), _params(technique_density=0.5), uuid4())
    assert len(roadmap_half.phases["phase_1"].techniques) == 2

    roadmap_zero = generate_roadmap(_research(), _template(), _params(technique_density=0.0), uuid4())
    assert len(roadmap_zero.phases["phase_1"].techniques) == 1


def test_session_count_mapping():
    t = _template()
    r = _research()

    low = generate_roadmap(r, t, _params(repetition_intensity=0.0), uuid4())
    med = generate_roadmap(r, t, _params(repetition_intensity=0.5), uuid4())
    high = generate_roadmap(r, t, _params(repetition_intensity=1.0), uuid4())

    assert low.phases["phase_1"].techniques[0].session_count == 1
    assert med.phases["phase_1"].techniques[0].session_count == 2
    assert high.phases["phase_1"].techniques[0].session_count == 3


def test_evidence_type_assignment():
    roadmap = generate_roadmap(_research(), _template(), _params(), uuid4())
    evidence_types = [cp.evidence_type for cp in roadmap.phases["phase_1"].checkpoints]
    assert evidence_types[0] == "artifact"
    assert evidence_types[1] == "numeric"
    assert evidence_types[2] == "behavioral_log"


def test_phase_ordering_only_first_active():
    roadmap = generate_roadmap(_research(), _template(), _params(), uuid4())
    statuses = [phase.status for phase in roadmap.phases.values()]
    assert statuses.count("active") == 1
    assert statuses[0] == "active"
    assert all(item == "locked" for item in statuses[1:])


def test_structured_template_is_primary_source():
    roadmap = generate_roadmap(_research(), _template_with_structured(), _params(), uuid4())
    phase = roadmap.phases["phase_1"]
    assert phase.competencies == ["line control", "shape accuracy"]
    assert phase.techniques[0].name == "Contour drill"
    assert [checkpoint.checkpoint_id for checkpoint in phase.checkpoints] == ["cp_percent", "cp_artifact"]
    assert phase.checkpoints[0].threshold == 0.85
    assert phase.checkpoints[0].evidence_type == "numeric"
    assert phase.checkpoints[1].evidence_type == "artifact"
