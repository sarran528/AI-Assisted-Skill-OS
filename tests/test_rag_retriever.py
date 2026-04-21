from backend.rag.retriever import lexical_score


def test_lexical_score_detects_overlap() -> None:
    score = lexical_score("blind contour drawing line quality", "This guide improves contour line quality in drawing drills")
    assert score > 0.2


def test_lexical_score_zero_for_no_overlap() -> None:
    score = lexical_score("gesture anatomy", "color grading and film exposure notes")
    assert score == 0.0
