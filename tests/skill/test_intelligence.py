"""Tests for skill intelligence engine."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.assessment.profile_vector import ProfileVector
from backend.shared.db.models.baseline_skill_state import BaselineSkillState
from backend.shared.db.models.skill_template import SkillTemplate
from backend.shared.llm.schemas import (
    DEFAULT_FEASIBILITY,
    DEFAULT_RISK_ZONES,
    DEFAULT_SKILL_MODIFIERS,
    DEFAULT_TIME_MODEL,
    FeasibilityResult,
    RiskZoneResult,
    SkillModifierResult,
    TimeModelResult,
)
from backend.skill.intelligence import SkillResearchObject, compute_skill_research
from backend.skill.intelligence_service import SkillIntelligenceService
from backend.shared.errors import BusinessError


@pytest.fixture
def profile_vector():
    """Create a test ProfileVector."""
    return ProfileVector(
        cognitive_capacity=0.7,
        attention_stability=0.8,
        learning_tolerance=0.6,
        motor_baseline=0.5,
        stress_resilience=0.75,
        time_constraint=0.9,
    )


@pytest.fixture
def baseline_skill_state():
    """Create a test BaselineSkillState."""
    return BaselineSkillState(
        skill_id="test-skill",
        user_id=uuid4(),
        exposure_score=0.75,
        declarative_score=0.8,
        confidence_score=0.7,
        perceived_level=0.75,
        actual_level=0.7,
        confidence_bias=0.05,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def skill_template():
    """Create a test SkillTemplate."""
    return MagicMock(spec=SkillTemplate)


@pytest.mark.asyncio
async def test_compute_skill_research_all_calls_made():
    """Test that all four LLM calls are made with correct parameters."""
    profile = ProfileVector(
        cognitive_capacity=0.8,
        attention_stability=0.7,
        learning_tolerance=0.6,
        motor_baseline=0.5,
        stress_resilience=0.75,
        time_constraint=0.9,
    )

    baseline = BaselineSkillState(
        skill_id="drawing",
        user_id=uuid4(),
        exposure_score=0.6,
        declarative_score=0.7,
        confidence_score=0.65,
        perceived_level=0.65,
        actual_level=0.8,
        confidence_bias=-0.15,
        created_at=datetime.utcnow(),
    )

    skill = MagicMock(spec=SkillTemplate)
    skill.skill_id = "drawing"
    skill.domain = "art"
    skill.complexity_score = 0.65
    skill.structure = {"phases": {"fundamentals": {}, "intermediate": {}}}

    mock_results = [
        DEFAULT_FEASIBILITY,
        DEFAULT_RISK_ZONES,
        DEFAULT_TIME_MODEL,
        DEFAULT_SKILL_MODIFIERS,
    ]

    with patch("backend.shared.llm.llm_call", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = mock_results

        result = await compute_skill_research(profile, baseline, skill)

        # Verify all four calls were made
        assert mock_llm.call_count == 4

        # Verify temperature was 0.0 for all calls
        for call in mock_llm.call_args_list:
            assert call[1]["temperature"] == 0.0

        # Verify schemas match
        assert mock_llm.call_args_list[0][1]["response_schema"] == FeasibilityResult
        assert mock_llm.call_args_list[1][1]["response_schema"] == RiskZoneResult
        assert mock_llm.call_args_list[2][1]["response_schema"] == TimeModelResult
        assert mock_llm.call_args_list[3][1]["response_schema"] == SkillModifierResult


@pytest.mark.asyncio
async def test_compute_skill_research_returns_complete_object(
    profile_vector, baseline_skill_state, skill_template
):
    """Test that SkillResearchObject is fully assembled with derived fields."""
    skill_template.skill_id = "python-basics"
    skill_template.domain = "programming"
    skill_template.complexity_score = 0.7

    mock_results = [
        FeasibilityResult(
            feasible=True, risk_level="medium", blockers=[], confidence=0.85
        ),
        DEFAULT_RISK_ZONES,
        TimeModelResult(estimated_weeks=10, hours_per_phase={}, confidence=0.7),
        DEFAULT_SKILL_MODIFIERS,
    ]

    with patch("backend.shared.llm.llm_call", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = mock_results

        result = await compute_skill_research(
            profile_vector, baseline_skill_state, skill_template
        )

        # Verify derived fields
        assert isinstance(result, SkillResearchObject)
        assert result.is_feasible is True
        assert result.estimated_weeks == 10
        assert result.overall_risk == "medium"
        assert result.confidence_bias == baseline_skill_state.confidence_bias


@pytest.mark.asyncio
async def test_compute_skill_research_with_fallback_values():
    """Test that object is assembled even when LLM calls use fallbacks."""
    profile = ProfileVector(0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
    baseline = BaselineSkillState(
        "test", uuid4(), 0.5, 0.5, 0.5, 0.5, 0.5, 0.0, datetime.utcnow()
    )
    skill = MagicMock(spec=SkillTemplate)
    skill.skill_id = "test"
    skill.domain = "other"
    skill.complexity_score = 0.5

    # All calls return fallbacks
    mock_results = [
        DEFAULT_FEASIBILITY,
        DEFAULT_RISK_ZONES,
        DEFAULT_TIME_MODEL,
        DEFAULT_SKILL_MODIFIERS,
    ]

    with patch("backend.shared.llm.llm_call", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = mock_results

        result = await compute_skill_research(profile, baseline, skill)

        # Should still produce valid object
        assert result.is_feasible is True  # From DEFAULT_FEASIBILITY
        assert result.estimated_weeks == 12  # From DEFAULT_TIME_MODEL
        assert result.overall_risk == "medium"  # From DEFAULT_FEASIBILITY


@pytest.mark.asyncio
async def test_skill_intelligence_service_generates_research(profile_vector):
    """Test full service flow with mocked repositories."""
    user_id = uuid4()
    skill_id = "drawing"

    # Create mock session and repositories
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock skill template
    mock_skill = MagicMock(spec=SkillTemplate)
    mock_skill.skill_id = skill_id
    mock_skill.domain = "art"
    mock_skill.complexity_score = 0.65

    # Mock baseline state
    mock_baseline = BaselineSkillState(
        skill_id=skill_id,
        user_id=user_id,
        exposure_score=0.6,
        declarative_score=0.7,
        confidence_score=0.65,
        perceived_level=0.65,
        actual_level=0.8,
        confidence_bias=-0.15,
        created_at=datetime.utcnow(),
    )

    with patch(
        "backend.skill.intelligence_service.SkillTemplateRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_active_template = AsyncMock(return_value=mock_skill)

        with patch(
            "backend.skill.intelligence_service.GroundingRepository"
        ) as mock_ground_class:
            mock_ground = MagicMock()
            mock_ground_class.return_value = mock_ground
            mock_ground.get_latest_baseline = AsyncMock(return_value=mock_baseline)

            with patch(
                "backend.skill.intelligence_service.compute_skill_research",
                new_callable=AsyncMock,
            ) as mock_compute:
                mock_research = SkillResearchObject(
                    skill_id=skill_id,
                    user_id=user_id,
                    profile_version=1,
                    feasibility=DEFAULT_FEASIBILITY,
                    risk_zones=DEFAULT_RISK_ZONES,
                    time_model=DEFAULT_TIME_MODEL,
                    skill_modifiers=DEFAULT_SKILL_MODIFIERS,
                    confidence_bias=-0.15,
                    is_feasible=True,
                    estimated_weeks=12,
                    overall_risk="medium",
                )
                mock_compute.return_value = mock_research

                with patch(
                    "backend.skill.intelligence_service.SkillResearchRepository.create",
                    new_callable=AsyncMock,
                ) as mock_persist:
                    with patch(
                        "backend.skill.intelligence_service.log_audit_event",
                        new_callable=AsyncMock,
                    ):
                        service = SkillIntelligenceService(mock_session)
                        result = await service.generate_skill_research(
                            user_id=user_id,
                            skill_id=skill_id,
                            profile=profile_vector,
                        )

                        # Verify result
                        assert result.skill_id == skill_id
                        assert result.is_feasible is True
                        assert result.estimated_weeks == 12

                        # Verify persistence was called
                        mock_persist.assert_called_once()


@pytest.mark.asyncio
async def test_service_raises_on_missing_skill():
    """Test that service raises BusinessError when skill not found."""
    mock_session = AsyncMock(spec=AsyncSession)

    with patch(
        "backend.skill.intelligence_service.SkillTemplateRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_active_template = AsyncMock(return_value=None)

        service = SkillIntelligenceService(mock_session)

        with pytest.raises(BusinessError):
            await service.generate_skill_research(
                user_id=uuid4(),
                skill_id="nonexistent",
                profile=ProfileVector(0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
            )


@pytest.mark.asyncio
async def test_service_raises_on_missing_baseline():
    """Test that service raises BusinessError when grounding not found."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_skill = MagicMock(spec=SkillTemplate)

    with patch(
        "backend.skill.intelligence_service.SkillTemplateRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_active_template = AsyncMock(return_value=mock_skill)

        with patch(
            "backend.skill.intelligence_service.GroundingRepository"
        ) as mock_ground_class:
            mock_ground = MagicMock()
            mock_ground_class.return_value = mock_ground
            mock_ground.get_latest_baseline = AsyncMock(return_value=None)

            service = SkillIntelligenceService(mock_session)

            with pytest.raises(BusinessError):
                await service.generate_skill_research(
                    user_id=uuid4(),
                    skill_id="test",
                    profile=ProfileVector(0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
                )
