"""
Validation service - validates evidence against thresholds.
"""
from typing import Optional


class ValidationService:
    """Validates evidence against checkpoint thresholds."""

    @staticmethod
    def validate_evidence(
        evidence_value: float,
        checkpoint_rigidity: float,
        evidence_type: str = "numeric",
    ) -> tuple[bool, dict]:
        """
        Validate evidence against threshold.
        
        Args:
            evidence_value: The captured/submitted value
            checkpoint_rigidity: Derived threshold from learning parameters
            evidence_type: Type of evidence (numeric, artifact, behavioral_log)
            
        Returns:
            (passed: bool, validation_result: dict)
        """
        if evidence_type != "numeric":
            # Non-numeric evidence defaults to validation based on presence
            return (True, {"type": evidence_type, "validated_at": str(__import__("datetime").datetime.utcnow())})

        # Numeric evidence: must meet or exceed threshold
        threshold = checkpoint_rigidity
        passed = evidence_value >= threshold

        return (
            passed,
            {
                "threshold": float(threshold),
                "actual_value": float(evidence_value),
                "passed": passed,
                "detail": f"Value {evidence_value} {'meets' if passed else 'does not meet'} threshold {threshold}",
            },
        )
