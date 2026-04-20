def normalize_score(raw: float, max_value: float) -> float:
    """Normalize a raw score to a 0..1 range."""
    if max_value <= 0:
        raise ValueError("max_value must be positive")
    return max(min(raw / max_value, 1.0), 0.0)
