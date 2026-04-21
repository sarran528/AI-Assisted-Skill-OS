def build_context_string(chunks: list[dict], max_chars: int = 6000) -> str:
    parts: list[str] = []
    total = 0
    for chunk in chunks:
        block = (
            f"[Source: {chunk.get('skill_id')} / {chunk.get('phase') or 'cross-phase'} / {chunk.get('doc_type')}]\n"
            f"{chunk.get('content', '')}\n"
        )
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts)
