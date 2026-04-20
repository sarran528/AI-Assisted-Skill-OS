"""
Skill template JSON schema validator.
Enforces structure for skill templates stored in database.
"""

from jsonschema import validate, ValidationError

SKILL_TEMPLATE_SCHEMA = {
    "type": "object",
    "required": ["phases"],
    "properties": {
        "phases": {
            "type": "object",
            "minProperties": 1,
            "additionalProperties": {
                "type": "object",
                "required": ["competencies", "techniques", "checkpoints"],
                "properties": {
                    "competencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1
                    },
                    "techniques": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1
                    },
                    "checkpoints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1
                    }
                }
            }
        },
        "grounding_probes": {
            "type": "object",
            "properties": {
                "recognition": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3
                },
                "familiarity": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["question", "options", "correct_index"],
                        "properties": {
                            "question": {"type": "string"},
                            "options": {"type": "array", "items": {"type": "string"}, "minItems": 2},
                            "correct_index": {"type": "integer", "minimum": 0}
                        }
                    },
                    "minItems": 3
                }
            }
        }
    }
}


def validate_template_structure(data: dict) -> None:
    """
    Validate skill template structure against schema.
    
    Args:
        data: Dictionary to validate
        
    Raises:
        ValidationError: If structure is invalid
    """
    validate(instance=data, schema=SKILL_TEMPLATE_SCHEMA)
