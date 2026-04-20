"""
Tests for skill template service.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.errors import BusinessError
from backend.skill.schemas import SkillTemplateCreate
from backend.skill.service import SkillTemplateService


@pytest.fixture
def valid_skill_create():
    """Valid skill template creation payload."""
    return SkillTemplateCreate(
        skill_id="drawing",
        name="Drawing",
        domain="art",
        complexity_score=0.65,
        structure={
            "phases": {
                "fundamentals": {
                    "competencies": ["line control"],
                    "techniques": ["drawing"],
                    "checkpoints": ["complete"]
                }
            }
        }
    )


@pytest.fixture
def invalid_skill_create():
    """Invalid skill template - missing checkpoints."""
    return SkillTemplateCreate(
        skill_id="invalid",
        name="Invalid Skill",
        domain="art",
        complexity_score=0.5,
        structure={
            "phases": {
                "fundamentals": {
                    "competencies": ["line control"],
                    "techniques": ["drawing"]
                    # Missing checkpoints
                }
            }
        }
    )


@pytest.mark.asyncio
async def test_create_valid_skill(db_session: AsyncSession, valid_skill_create):
    """Creating a valid skill should succeed."""
    service = SkillTemplateService(db_session)
    template = await service.create_skill_template(valid_skill_create)
    
    assert template.skill_id == "drawing"
    assert template.name == "Drawing"
    assert template.domain == "art"
    assert float(template.complexity_score) == 0.65
    assert template.version == 1
    assert template.is_active is True


@pytest.mark.asyncio
async def test_create_invalid_skill_structure_fails(
    db_session: AsyncSession, invalid_skill_create
):
    """Creating skill with invalid structure should raise BusinessError."""
    service = SkillTemplateService(db_session)
    
    with pytest.raises(BusinessError) as exc_info:
        await service.create_skill_template(invalid_skill_create)
    
    assert exc_info.value.code == "invalid_template_structure"


@pytest.mark.asyncio
async def test_get_nonexistent_skill_fails(db_session: AsyncSession):
    """Getting nonexistent skill should raise BusinessError."""
    service = SkillTemplateService(db_session)
    
    with pytest.raises(BusinessError) as exc_info:
        await service.get_skill("nonexistent")
    
    assert exc_info.value.code == "skill_not_found"


@pytest.mark.asyncio
async def test_create_then_get_skill(db_session: AsyncSession, valid_skill_create):
    """Create a skill then retrieve it."""
    service = SkillTemplateService(db_session)
    
    # Create
    created = await service.create_skill_template(valid_skill_create)
    assert created.skill_id == "drawing"
    
    # Get
    retrieved = await service.get_skill("drawing")
    assert retrieved.skill_id == "drawing"
    assert retrieved.version == 1
    assert retrieved.id == created.id


@pytest.mark.asyncio
async def test_create_second_version_deactivates_first(
    db_session: AsyncSession, valid_skill_create
):
    """Creating second version should deactivate first version."""
    service = SkillTemplateService(db_session)
    
    # Create first version
    v1 = await service.create_skill_template(valid_skill_create)
    assert v1.version == 1
    assert v1.is_active is True
    
    # Create second version
    v2_data = SkillTemplateCreate(
        skill_id="drawing",
        name="Drawing - Updated",
        domain="art",
        complexity_score=0.70,
        structure={
            "phases": {
                "fundamentals": {
                    "competencies": ["line control", "shapes"],
                    "techniques": ["drawing"],
                    "checkpoints": ["complete"]
                }
            }
        }
    )
    v2 = await service.create_skill_template(v2_data)
    
    assert v2.version == 2
    assert v2.is_active is True
    assert v2.name == "Drawing - Updated"
    
    # Get should return v2
    retrieved = await service.get_skill("drawing")
    assert retrieved.version == 2


@pytest.mark.asyncio
async def test_list_skills_empty(db_session: AsyncSession):
    """Listing skills when empty should return empty list."""
    service = SkillTemplateService(db_session)
    skills = await service.list_skills()
    assert skills == []


@pytest.mark.asyncio
async def test_list_skills_multiple(db_session: AsyncSession):
    """Listing multiple skills should return all."""
    service = SkillTemplateService(db_session)
    
    # Create two skills
    drawing = SkillTemplateCreate(
        skill_id="drawing",
        name="Drawing",
        domain="art",
        complexity_score=0.65,
        structure={
            "phases": {
                "fundamentals": {
                    "competencies": ["line"],
                    "techniques": ["drawing"],
                    "checkpoints": ["complete"]
                }
            }
        }
    )
    
    python = SkillTemplateCreate(
        skill_id="python",
        name="Python",
        domain="programming",
        complexity_score=0.55,
        structure={
            "phases": {
                "basics": {
                    "competencies": ["syntax"],
                    "techniques": ["coding"],
                    "checkpoints": ["complete"]
                }
            }
        }
    )
    
    await service.create_skill_template(drawing)
    await service.create_skill_template(python)
    
    # List
    skills = await service.list_skills()
    assert len(skills) == 2
    skill_ids = {s.skill_id for s in skills}
    assert skill_ids == {"drawing", "python"}


@pytest.mark.asyncio
async def test_skill_mapping_validation_errors(db_session: AsyncSession):
    """Skill with invalid structure should fail validation."""
    service = SkillTemplateService(db_session)
    
    invalid = SkillTemplateCreate(
        skill_id="invalid",
        name="Invalid",
        domain="art",
        complexity_score=0.5,
        structure={
            "phases": {
                "phase1": {
                    "competencies": [],  # Empty - should fail
                    "techniques": ["t"],
                    "checkpoints": ["c"]
                }
            }
        }
    )
    
    with pytest.raises(BusinessError):
        await service.create_skill_template(invalid)
