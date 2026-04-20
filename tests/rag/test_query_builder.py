from backend.rag.query_builder import build_doubt_query, build_resource_query, build_tip_query


def test_build_resource_query_contract() -> None:
    query = build_resource_query("drawing", "fundamentals", None)
    assert query.top_k == 5
    assert query.doc_type_filter == ["tutorial", "resource"]


def test_build_doubt_query_contract() -> None:
    query = build_doubt_query("drawing", "fundamentals", "line_control", "how do i fix pressure")
    assert query.top_k == 7
    assert query.doc_type_filter is None
    assert "how do i fix pressure" in query.query_text


def test_build_tip_query_contract() -> None:
    query = build_tip_query("drawing", "line_control", "accuracy_below_threshold")
    assert query.top_k == 3
    assert query.doc_type_filter == ["failure_analysis", "technique_guide"]
