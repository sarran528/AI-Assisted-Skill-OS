import pytest

from backend.validation.calculations import normalize_score


def test_normalize_score_clamps() -> None:
    assert normalize_score(5, 10) == 0.5
    assert normalize_score(15, 10) == 1.0
    assert normalize_score(-1, 10) == 0.0


def test_normalize_score_rejects_zero() -> None:
    with pytest.raises(ValueError):
        normalize_score(1, 0)
