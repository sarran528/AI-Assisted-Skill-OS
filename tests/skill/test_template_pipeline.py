from backend.skill.template_pipeline import (
    REQUIRED_PHASES,
    build_queries,
    deduplicate_texts,
    filter_urls,
    to_legacy_structure,
    to_skill_id,
    validate_template,
)


def _valid_template() -> dict:
    phase_block = {
        "competencies": ["core control"],
        "techniques": [
            {
                "id": "tech_1",
                "name": "Technique 1",
                "protocol_steps": ["step 1", "step 2"],
                "checkpoints": [
                    {
                        "id": "cp_1",
                        "competency_target": "control",
                        "target_metric": "accuracy %",
                        "threshold": ">= 80%",
                        "validation_method": "numeric",
                        "failure_condition": "< 80% accuracy",
                    }
                ],
            }
        ],
    }
    return {
        "skill_id": "python_basics",
        "phases": {name: phase_block for name in REQUIRED_PHASES},
    }


def test_build_queries_returns_five_queries() -> None:
    queries = build_queries("Python Basics")
    assert len(queries) == 5
    assert "Python Basics" in queries[0]


def test_filter_urls_removes_blocked_domains() -> None:
    urls = [
        "https://example.com/guide",
        "https://reddit.com/r/learnpython",
        "https://youtube.com/watch?v=1",
    ]
    filtered = filter_urls(urls)
    assert filtered == ["https://example.com/guide"]


def test_deduplicate_texts_removes_duplicates() -> None:
    base = "a" * 900
    deduped = deduplicate_texts([base, base, "b" * 900])
    assert len(deduped) == 2


def test_validate_template_accepts_valid_strict_template() -> None:
    valid, reason = validate_template(_valid_template())
    assert valid is True
    assert reason == "valid"


def test_validate_template_rejects_non_numeric_threshold() -> None:
    template = _valid_template()
    template["phases"]["fundamentals"]["techniques"][0]["checkpoints"][0]["threshold"] = "good understanding"
    valid, reason = validate_template(template)
    assert valid is False
    assert "not numeric" in reason


def test_to_legacy_structure_projects_for_roadmap() -> None:
    legacy = to_legacy_structure(_valid_template())
    assert "phases" in legacy
    assert "technique_definitions" in legacy
    assert legacy["phases"]["fundamentals"]["techniques"] == ["Technique 1"]
    assert to_skill_id("Data Science 101") == "data_science_101"
