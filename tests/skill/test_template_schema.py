"""
Tests for skill template schema validation.
"""

import pytest
from jsonschema import ValidationError

from backend.skill.template_schema import (
    validate_template_structure,
    SKILL_TEMPLATE_SCHEMA,
)


@pytest.fixture
def valid_template():
    """Valid skill template structure."""
    return {
        "phases": {
            "fundamentals": {
                "competencies": ["line control", "basic shapes"],
                "techniques": ["blind contour", "gesture drawing"],
                "checkpoints": ["complete 3 drawings"]
            }
        }
    }


@pytest.fixture
def valid_template_with_probes():
    """Valid template with grounding probes."""
    return {
        "phases": {
            "fundamentals": {
                "competencies": ["line control"],
                "techniques": ["drawing"],
                "checkpoints": ["complete"]
            }
        },
        "grounding_probes": {
            "recognition": ["item1", "item2", "item3"],
            "familiarity": [
                {
                    "question": "What is drawing?",
                    "options": ["painting", "drawing", "sculpting"],
                    "correct_index": 1
                },
                {
                    "question": "What is shading?",
                    "options": ["coloring", "shading", "blending"],
                    "correct_index": 1
                },
                {
                    "question": "What is perspective?",
                    "options": ["view", "perspective", "distance"],
                    "correct_index": 1
                }
            ]
        }
    }


def test_valid_template_passes(valid_template):
    """Valid template should pass validation."""
    # Should not raise
    validate_template_structure(valid_template)


def test_valid_template_with_probes_passes(valid_template_with_probes):
    """Valid template with probes should pass validation."""
    validate_template_structure(valid_template_with_probes)


def test_missing_phases_fails(valid_template):
    """Missing 'phases' key should raise ValidationError."""
    del valid_template["phases"]
    with pytest.raises(ValidationError):
        validate_template_structure(valid_template)


def test_missing_competencies_fails(valid_template):
    """Missing 'competencies' in phase should raise ValidationError."""
    del valid_template["phases"]["fundamentals"]["competencies"]
    with pytest.raises(ValidationError):
        validate_template_structure(valid_template)


def test_missing_techniques_fails(valid_template):
    """Missing 'techniques' in phase should raise ValidationError."""
    del valid_template["phases"]["fundamentals"]["techniques"]
    with pytest.raises(ValidationError):
        validate_template_structure(valid_template)


def test_missing_checkpoints_fails(valid_template):
    """Missing 'checkpoints' in phase should raise ValidationError."""
    del valid_template["phases"]["fundamentals"]["checkpoints"]
    with pytest.raises(ValidationError):
        validate_template_structure(valid_template)


def test_empty_competencies_fails(valid_template):
    """Empty 'competencies' array should raise ValidationError."""
    valid_template["phases"]["fundamentals"]["competencies"] = []
    with pytest.raises(ValidationError):
        validate_template_structure(valid_template)


def test_empty_techniques_fails(valid_template):
    """Empty 'techniques' array should raise ValidationError."""
    valid_template["phases"]["fundamentals"]["techniques"] = []
    with pytest.raises(ValidationError):
        validate_template_structure(valid_template)


def test_empty_checkpoints_fails(valid_template):
    """Empty 'checkpoints' array should raise ValidationError."""
    valid_template["phases"]["fundamentals"]["checkpoints"] = []
    with pytest.raises(ValidationError):
        validate_template_structure(valid_template)


def test_wrong_type_competencies_fails(valid_template):
    """Non-string items in competencies should raise ValidationError."""
    valid_template["phases"]["fundamentals"]["competencies"] = [1, 2, 3]
    with pytest.raises(ValidationError):
        validate_template_structure(valid_template)


def test_wrong_type_phases_fails(valid_template):
    """Non-dict phases should raise ValidationError."""
    valid_template["phases"] = ["not", "a", "dict"]
    with pytest.raises(ValidationError):
        validate_template_structure(valid_template)


def test_multiple_phases_valid(valid_template):
    """Template with multiple phases should be valid."""
    valid_template["phases"]["intermediate"] = {
        "competencies": ["shading"],
        "techniques": ["hatching"],
        "checkpoints": ["shade a sphere"]
    }
    # Should not raise
    validate_template_structure(valid_template)


def test_invalid_probe_familiarity_missing_question_fails(valid_template):
    """Probe without 'question' field should fail."""
    valid_template["grounding_probes"] = {
        "familiarity": [
            {
                "options": ["a", "b"],
                "correct_index": 0
            }
        ]
    }
    with pytest.raises(ValidationError):
        validate_template_structure(valid_template)


def test_extra_fields_allowed(valid_template):
    """Extra fields beyond schema should be allowed (additionalProperties)."""
    valid_template["extra_metadata"] = {"custom": "data"}
    # Should not raise
    validate_template_structure(valid_template)
