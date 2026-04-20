from __future__ import annotations


def build_doubt_prompt(
    context: str,
    question: str,
    skill_id: str,
    phase: str | None,
    technique: str | None,
) -> str:
    return (
        f"You are a learning assistant for the skill: {skill_id}.\n"
        f"The learner is currently in the {phase or 'unknown'} phase, working on: {technique or 'unknown'}.\n\n"
        "Use ONLY the following reference material to answer the question.\n"
        "Do not use any knowledge outside of the provided context.\n"
        "If the context does not contain enough information to answer, say so clearly.\n\n"
        "Return strict JSON with keys: answer, source_phases, confidence, caveat.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION:\n{question}\n\n"
        "Respond with a concise, specific answer in 2-4 sentences. No preamble."
    )


def build_tip_prompt(context: str, technique_id: str, failure_type: str, attempt_number: int) -> str:
    return (
        f"You are providing a targeted correction for a learner who is failing at: {technique_id}.\n"
        f"Failure type: {failure_type}\n"
        f"Number of failed attempts: {attempt_number}\n\n"
        "Use ONLY the following reference material.\n"
        "Provide ONE specific, actionable correction. Maximum 2 sentences.\n"
        "Do not explain why this matters. Do not provide encouragement. Just the correction.\n"
        "Return strict JSON with keys: tip, target_step, severity.\n\n"
        f"CONTEXT:\n{context}\n\n"
        "Tip:"
    )
