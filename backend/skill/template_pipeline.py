"""Structured skill template retrieval and synthesis pipeline."""

from __future__ import annotations

import hashlib
import json
import logging
import random
import re
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
import numpy as np
import tiktoken
from openai import AsyncOpenAI
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.config import settings
from backend.shared.db.models import RagChunk

logger = logging.getLogger(__name__)

REQUIRED_PHASES = ["fundamentals", "intermediate", "advanced", "application", "mastery"]
NUMERIC_SIGNALS = ["%", "seconds", "count", "errors", "ms", "rate", ">=", "<=", "<", ">"]
BLOCKED_DOMAINS = {"reddit.com", "quora.com", "pinterest.com", "youtube.com"}
PREFERRED_SIGNALS = ("tutorial", "guide", "learn", "course", "docs", "practice")
MAX_QUERY_COUNT = 5
MAX_URLS = 10
MIN_SOURCE_LENGTH = 800
CONTENT_CAP = 12000

PASS_1_PROMPT = """
You are a concept extraction engine.
Extract learning objectives, techniques, and progression from the provided content.

CRITICAL: Return ONLY valid JSON with NO explanation, NO markdown, NO code blocks.

Output exactly:
{
  "core_concepts": ["concept1", "concept2"],
  "intermediate_concepts": ["concept3", "concept4"],
  "advanced_concepts": ["concept5"],
  "techniques": [
    {
      "name": "technique name",
      "difficulty": "beginner",
      "steps": ["step1", "step2", "step3"]
    }
  ],
  "failure_modes": ["common mistake 1", "common mistake 2"],
  "progression_order": ["concept1", "concept2", "concept3"],
  "estimated_hours_fundamentals": 20,
  "estimated_hours_intermediate": 30,
  "estimated_hours_advanced": 40,
  "estimated_hours_application": 25,
  "estimated_hours_mastery": 20
}
"""

PASS_2_PROMPT = """
You are a SkillTemplate construction engine.
Convert the extracted concepts into a strict SkillTemplate JSON object.

CRITICAL RULES:
- Return ONLY valid JSON. No preamble. No explanation. No markdown code blocks.
- Phases MUST be exactly: fundamentals, intermediate, advanced, application, mastery (ALL 5 required)
- Each phase MUST have 2-4 techniques
- Each technique MUST have 1-3 checkpoints
- EVERY checkpoint MUST have these exact fields: id, competency_target, target_metric, threshold, validation_method, failure_condition
- target_metric and threshold MUST be quantifiable with numeric signals like: %, seconds, count, errors, ms, rate, >=, <=, <, >
  Examples: ">= 85%", "< 3 errors", "<= 30 seconds", ">= 5 completed"
- NEVER use vague metrics like "understand", "improve", "learn" — these will FAIL validation
- Difficulty must increase across phases
- validation_method must be one of: numeric, artifact, behavioral_log

SCHEMA:
{
  "phases": {
    "fundamentals": {
      "competencies": ["string"],
      "techniques": [
        {
          "id": "tech-1",
          "name": "string",
          "protocol_steps": ["step 1", "step 2"],
          "checkpoints": [
            {
              "id": "cp-1",
              "competency_target": "string",
              "target_metric": "accuracy %, time in seconds, count, or error rate",
              "threshold": "numeric comparison like >= 80%",
              "validation_method": "numeric|artifact|behavioral_log",
              "failure_condition": "specific condition like < 70% accuracy"
            }
          ]
        }
      ]
    },
    "intermediate": { ... },
    "advanced": { ... },
    "application": { ... },
    "mastery": { ... }
  }
}

EXAMPLE for Java - fundamentals phase:
{
  "phases": {
    "fundamentals": {
      "competencies": ["variables", "data types", "operators"],
      "techniques": [
        {
          "id": "variables-101",
          "name": "Variable Declaration and Assignment",
          "protocol_steps": ["declare int variable", "assign value", "print to console"],
          "checkpoints": [
            {
              "id": "var-cp-1",
              "competency_target": "Declare and assign primitive types",
              "target_metric": "accuracy percentage",
              "threshold": ">= 80%",
              "validation_method": "numeric",
              "failure_condition": "< 80% accuracy on 10 variable declarations"
            }
          ]
        }
      ]
    },
    ...all 5 phases required...
  }
}
"""


def to_skill_id(skill_name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s_-]+", "", skill_name).strip().lower()
    return re.sub(r"[\s-]+", "_", cleaned)


MULTI_QUERY_TEMPLATES = [
    "{skill_name} complete learning roadmap",
    "{skill_name} prerequisites beginner",
    "{skill_name} common mistakes learners make",
    "{skill_name} how long to learn",
    "{skill_name} best resources tutorials",
    "{skill_name} job requirements professional",
]


def build_queries(skill_name: str) -> list[str]:
    return [template.format(skill_name=skill_name) for template in MULTI_QUERY_TEMPLATES]


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def filter_urls(urls: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for url in urls:
        domain = _domain(url)
        if any(blocked in domain for blocked in BLOCKED_DOMAINS):
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append(url)
    return out


def deduplicate_texts(texts: list[str]) -> list[str]:
    seen = set()
    unique: list[str] = []
    for text in texts:
        digest = hashlib.md5(text[:500].encode("utf-8")).hexdigest()
        if digest not in seen:
            seen.add(digest)
            unique.append(text)
    return unique


def get_content_hash(combined_text: str) -> str:
    return hashlib.md5(combined_text.encode("utf-8")).hexdigest()


def validate_template(template: dict[str, Any]) -> tuple[bool, str]:
    if "skill_id" not in template:
        return False, "Missing skill_id"
    if "phases" not in template:
        return False, "Missing phases block"
    if not isinstance(template["phases"], dict):
        return False, "phases must be an object"

    for phase in REQUIRED_PHASES:
        if phase not in template["phases"]:
            return False, f"Missing required phase: {phase}"

    for phase_name, phase_data in template["phases"].items():
        if not isinstance(phase_data, dict):
            return False, f"Phase '{phase_name}' is invalid"
        techniques = phase_data.get("techniques", [])
        if not isinstance(techniques, list) or len(techniques) == 0:
            return False, f"Phase '{phase_name}' has no techniques"
        if len(techniques) > 4:
            return False, f"Phase '{phase_name}' exceeds 4 technique limit"

        for technique in techniques:
            checkpoints = technique.get("checkpoints", []) if isinstance(technique, dict) else []
            if len(checkpoints) == 0:
                return False, f"Technique '{technique.get('id') if isinstance(technique, dict) else 'unknown'}' has no checkpoints"
            if len(checkpoints) > 3:
                return False, f"Technique '{technique.get('id') if isinstance(technique, dict) else 'unknown'}' exceeds 3 checkpoint limit"

            for checkpoint in checkpoints:
                required = {
                    "id",
                    "competency_target",
                    "target_metric",
                    "threshold",
                    "validation_method",
                    "failure_condition",
                }
                if not isinstance(checkpoint, dict):
                    return False, "checkpoint must be an object"
                missing = required - set(checkpoint.keys())
                if missing:
                    return False, f"Checkpoint missing fields: {missing}"
                threshold = str(checkpoint.get("threshold", ""))
                if not any(sig in threshold for sig in NUMERIC_SIGNALS):
                    return False, f"Checkpoint '{checkpoint['id']}' threshold is not numeric: '{threshold}'"
    return True, "valid"


@dataclass
class StructuredTemplateResult:
    template: dict[str, Any]
    content_hash: str
    version: str


@dataclass
class _FaissAssets:
    index: Any
    id_map: list[str]
    metadata: dict[str, dict[str, Any]]


@dataclass
class _RetrievedSource:
    url: str
    content: str
    doc_type: str = "web_article"
    phase: str | None = None


class SkillTemplatePipeline:
    """Builds schema-enforced skill templates from external web content."""

    def __init__(self, db_session: AsyncSession | None = None) -> None:
        self._http = httpx.AsyncClient(timeout=12.0)
        self._cache: dict[str, StructuredTemplateResult] = {}
        self._embedder = self._init_embedder()
        self._faiss_assets = self._init_faiss_assets()
        self._db_session = db_session

    async def close(self) -> None:
        await self._http.aclose()

    async def _with_backoff(self, fn, retries: int = 3, base_delay: float = 1.5):  # type: ignore[no-untyped-def]
        for attempt in range(retries):
            try:
                return await fn()
            except Exception:
                if attempt == retries - 1:
                    return None
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                await self._sleep(delay)
        return None

    async def _sleep(self, seconds: float) -> None:
        # test-friendly isolated sleep
        await asyncio.sleep(seconds)

    def _init_embedder(self) -> Any | None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            return SentenceTransformer(settings.local_embedding_model)
        except Exception:
            return None

    def _init_faiss_assets(self) -> _FaissAssets | None:
        try:
            import faiss  # type: ignore
        except Exception:
            return None

        index_path = Path(settings.faiss_index_path)
        metadata_path = Path(settings.faiss_metadata_path)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        if self._embedder is None:
            return None

        try:
            sample_embedding = self._embedder.encode(["dimension_probe"])[0]
            dim = int(len(sample_embedding))
        except Exception:
            dim = 384

        if index_path.exists():
            index = faiss.read_index(str(index_path))
        else:
            index = faiss.IndexFlatL2(dim)

        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            id_map = list(metadata.get("_id_map", []))
        else:
            metadata = {"_id_map": []}
            id_map = []
        return _FaissAssets(index=index, id_map=id_map, metadata=metadata)

    def _persist_faiss_assets(self) -> None:
        assets = self._faiss_assets
        if assets is None:
            return
        try:
            import faiss  # type: ignore
        except Exception:
            return
        index_path = Path(settings.faiss_index_path)
        metadata_path = Path(settings.faiss_metadata_path)
        assets.metadata["_id_map"] = assets.id_map
        faiss.write_index(assets.index, str(index_path))
        metadata_path.write_text(json.dumps(assets.metadata, indent=2), encoding="utf-8")

    def _store_in_faiss(self, result: StructuredTemplateResult, skill_name: str) -> None:
        assets = self._faiss_assets
        if assets is None or self._embedder is None:
            return
        skill_id = result.template["skill_id"]
        if skill_id in assets.metadata:
            assets.metadata[skill_id] = {
                "version": result.version,
                "content_hash": result.content_hash,
            }
            self._persist_faiss_assets()
            return
        embedding = self._embedder.encode([skill_name])[0].astype(np.float32)
        assets.index.add(embedding.reshape(1, -1))
        assets.id_map.append(skill_id)
        assets.metadata[skill_id] = {
            "version": result.version,
            "content_hash": result.content_hash,
        }
        self._persist_faiss_assets()

    async def search_serper(self, query: str, num: int = 5) -> list[str]:
        if not settings.serper_api_key:
            return []
        payload = {"q": query, "num": num}
        headers = {"X-API-KEY": settings.serper_api_key, "Content-Type": "application/json"}
        response = await self._http.post("https://google.serper.dev/search", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return [entry["link"] for entry in data.get("organic", []) if "link" in entry]

    async def search_serpapi(self, query: str, num: int = 5) -> list[str]:
        if not settings.serpapi_api_key:
            return []
        params = {
            "engine": "google",
            "q": query,
            "num": num,
            "api_key": settings.serpapi_api_key,
        }
        response = await self._http.get("https://serpapi.com/search.json", params=params)
        response.raise_for_status()
        data = response.json()
        return [entry["link"] for entry in data.get("organic_results", []) if "link" in entry]

    async def search_web(self, query: str, num: int = 5) -> list[str]:
        provider = settings.search_provider.strip().lower()
        if provider == "serpapi":
            return await self.search_serpapi(query, num=num)
        return await self.search_serper(query, num=num)

    async def extract_text(self, url: str) -> str | None:
        try:
            from newspaper import Article  # type: ignore

            article = Article(url)
            article.download()
            article.parse()
            text = article.text.strip()
            if len(text) > MIN_SOURCE_LENGTH:
                return text
        except Exception:
            pass

        try:
            response = await self._http.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text(" ", strip=True) for p in paragraphs).strip()
            if len(text) > MIN_SOURCE_LENGTH:
                return text
        except Exception:
            return None
        return None

    def _chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 64) -> list[tuple[str, int]]:
        """Chunk text by tokens and return (chunk_text, token_count)."""
        if not text.strip():
            return []
        if overlap >= chunk_size:
            overlap = max(0, chunk_size // 4)
        try:
            encoding = tiktoken.encoding_for_model(settings.embedding_model)
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        if not tokens:
            return []

        step = max(1, chunk_size - overlap)
        chunks: list[tuple[str, int]] = []
        for start in range(0, len(tokens), step):
            token_slice = tokens[start : start + chunk_size]
            if not token_slice:
                break
            chunk_text = encoding.decode(token_slice).strip()
            if chunk_text:
                chunks.append((chunk_text, len(token_slice)))
            if start + chunk_size >= len(tokens):
                break
        return chunks

    async def _embed_text(self, text: str) -> list[float] | None:
        if not settings.openai_api_key:
            return None
        try:
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.embeddings.create(
                model=settings.embedding_model,
                input=[text],
            )
            return response.data[0].embedding
        except Exception:
            return None

    async def _index_sources_in_pgvector(self, skill_id: str, sources: list[_RetrievedSource]) -> None:
        if self._db_session is None:
            return
        payload: list[dict[str, Any]] = []
        for source in sources:
            chunks = self._chunk_text(source.content, chunk_size=512, overlap=64)
            for chunk_index, (chunk_text, token_count) in enumerate(chunks):
                embedding = await self._embed_text(chunk_text)
                if embedding is None:
                    continue
                payload.append(
                    {
                        "skill_id": skill_id,
                        "phase": source.phase,
                        "technique_id": None,
                        "doc_type": source.doc_type,
                        "source_url": source.url,
                        "chunk_index": chunk_index,
                        "content": chunk_text,
                        "embedding": embedding,
                        "model_name": settings.embedding_model,
                        "token_count": token_count,
                    }
                )

        if not payload:
            return

        stmt = insert(RagChunk).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=["skill_id", "source_url", "chunk_index"],
            set_={
                "phase": stmt.excluded.phase,
                "doc_type": stmt.excluded.doc_type,
                "content": stmt.excluded.content,
                "embedding": stmt.excluded.embedding,
                "model_name": stmt.excluded.model_name,
                "token_count": stmt.excluded.token_count,
            },
        )
        await self._db_session.execute(stmt)
        await self._db_session.flush()

    async def _call_openai_compatible_json(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        system_prompt: str,
        content: str,
        max_tokens: int,
    ) -> dict[str, Any] | None:
        if not api_key:
            return None
        payload = {
            "model": model,
            "temperature": 0,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = await self._http.post(base_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        raw = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def _structured_llm_call(
        self, *, system_prompt: str, content: str, max_tokens: int = 4000
    ) -> dict[str, Any] | None:
        # Primary: Groq
        groq_result = await self._with_backoff(
            lambda: self._call_openai_compatible_json(
                base_url="https://api.groq.com/openai/v1/chat/completions",
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                system_prompt=system_prompt,
                content=content,
                max_tokens=max_tokens,
            ),
            retries=2,
            base_delay=1.0,
        )
        if groq_result is not None:
            return groq_result

        # Fallback: Together AI
        return await self._with_backoff(
            lambda: self._call_openai_compatible_json(
                base_url="https://api.together.xyz/v1/chat/completions",
                api_key=settings.together_api_key,
                model=settings.together_model,
                system_prompt=system_prompt,
                content=content,
                max_tokens=max_tokens,
            ),
            retries=2,
            base_delay=1.0,
        )

    async def structure_template_two_pass(self, skill_name: str, raw_content: str) -> dict[str, Any] | None:
        pass1_payload = f"Skill: {skill_name}\n\nContent:\n{raw_content[:CONTENT_CAP]}"
        extracted = await self._structured_llm_call(system_prompt=PASS_1_PROMPT, content=pass1_payload, max_tokens=2000)
        if extracted is None:
            logger.warning(f"Pass 1 (concept extraction) failed for skill '{skill_name}'")
            return None

        logger.debug(f"Pass 1 output for '{skill_name}': {json.dumps(extracted)[:500]}")

        pass2_payload = f"Skill: {skill_name}\n\nExtracted Data:\n{json.dumps(extracted)}"
        result = await self._structured_llm_call(system_prompt=PASS_2_PROMPT, content=pass2_payload, max_tokens=4000)
        
        if result is None:
            logger.warning(f"Pass 2 (template synthesis) failed for skill '{skill_name}'")
            return None
        
        logger.debug(f"Pass 2 output for '{skill_name}': {json.dumps(result)[:500]}")
        return result

    async def _attempt_build(
        self,
        *,
        skill_name: str,
        query_limit: int,
        query_num: int,
        url_limit: int,
        min_length: int,
        query_delay: float,
    ) -> StructuredTemplateResult | None:
        queries = build_queries(skill_name)[:query_limit]
        
        # Parallel SERP searches
        search_tasks = [self._with_backoff(lambda q=query: self.search_web(q, num=query_num)) for query in queries]
        all_url_sets = await asyncio.gather(*search_tasks)
        
        all_urls: list[str] = []
        for urls in all_url_sets:
            if urls:
                all_urls.extend(filter_urls(urls))

        retrieved_sources: list[_RetrievedSource] = []
        # Parallel extraction
        extract_tasks = [self._with_backoff(lambda u=url: self.extract_text(u)) for url in all_urls[:url_limit]]
        extracted_texts = await asyncio.gather(*extract_tasks)
        
        for i, text in enumerate(extracted_texts):
            if text and len(text) > min_length:
                retrieved_sources.append(_RetrievedSource(url=all_urls[i], content=text))

        deduped_sources: list[_RetrievedSource] = []
        seen_hashes: set[str] = set()
        for source in retrieved_sources:
            digest = hashlib.md5(source.content[:500].encode("utf-8")).hexdigest()
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            deduped_sources.append(source)

        if len(deduped_sources) < 2:
            return None

        combined = "\n\n---\n\n".join(source.content for source in deduped_sources)
        content_hash = get_content_hash(combined)
        skill_id = to_skill_id(skill_name)

        cached = self._cache.get(skill_id)
        if cached and cached.content_hash == content_hash:
            return cached

        template = await self.structure_template_two_pass(skill_name, combined)
        if template is None:
            return None
        template["skill_id"] = skill_id
        valid, reason = validate_template(template)
        if not valid:
            logger.warning(f"Template validation failed for '{skill_name}': {reason}")
            logger.debug(f"Invalid template: {json.dumps(template)[:500]}")
            return None

        version = hashlib.md5(json.dumps(template, sort_keys=True).encode("utf-8")).hexdigest()[:8]
        result = StructuredTemplateResult(template=template, content_hash=content_hash, version=version)
        self._cache[skill_id] = result
        self._store_in_faiss(result, skill_name)
        await self._index_sources_in_pgvector(skill_id, deduped_sources)
        return result

    async def aggregate_serp_context(self, skill_name: str) -> dict[str, Any]:
        """Stage 3: Raw Data Aggregation for LLM input."""
        queries = build_queries(skill_name)
        search_tasks = [self._with_backoff(lambda q=query: self.search_web(q, num=3)) for query in queries]
        all_url_sets = await asyncio.gather(*search_tasks)
        
        url_map: dict[str, list[str]] = {}
        for i, urls in enumerate(all_url_sets):
            if urls:
                url_map[MULTI_QUERY_TEMPLATES[i]] = filter_urls(urls)

        # Parallel extraction of top 2 URLs per query
        all_target_urls = []
        for urls in url_map.values():
            all_target_urls.extend(urls[:2])
        
        all_target_urls = list(set(all_target_urls))[:10] # Unique top URLs
        extract_tasks = [self._with_backoff(lambda u=url: self.extract_text(u)) for url in all_target_urls]
        extracted_texts = await asyncio.gather(*extract_tasks)
        
        # Structure the context
        context_blocks = []
        for i, text in enumerate(extracted_texts):
            if text:
                # Basic cleaning: strip extra whitespace and short lines
                lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 40]
                cleaned_text = " ".join(lines[:50]) # First 50 relevant lines
                context_blocks.append({
                    "url": all_target_urls[i],
                    "content": cleaned_text
                })
        
        return {
            "skill_name": skill_name,
            "research_timestamp": datetime.utcnow().isoformat(),
            "sources": context_blocks
        }

    async def build_with_fallback(self, skill_name: str) -> StructuredTemplateResult | None:
        primary = await self._attempt_build(
            skill_name=skill_name,
            query_limit=MAX_QUERY_COUNT,
            query_num=5,
            url_limit=MAX_URLS,
            min_length=MIN_SOURCE_LENGTH,
            query_delay=1.5,
        )
        if primary:
            return primary
        return await self._attempt_build(
            skill_name=skill_name,
            query_limit=3,
            query_num=3,
            url_limit=6,
            min_length=1200,
            query_delay=2.0,
        )


def to_legacy_structure(structured_template: dict[str, Any]) -> dict[str, Any]:
    """Project strict SkillTemplate shape into legacy roadmap-compatible structure."""
    phases = structured_template.get("phases", {})
    legacy_phases: dict[str, Any] = {}
    technique_definitions: dict[str, Any] = {}

    for phase_name, phase_data in phases.items():
        techniques = phase_data.get("techniques", [])
        legacy_phases[phase_name] = {
            "competencies": phase_data.get("competencies", []),
            "techniques": [technique.get("name", technique.get("id", "technique")) for technique in techniques],
            "checkpoints": [
                checkpoint.get("competency_target", checkpoint.get("target_metric", "checkpoint"))
                for technique in techniques
                for checkpoint in technique.get("checkpoints", [])
            ],
        }
        for technique in techniques:
            technique_name = technique.get("name", technique.get("id", "technique"))
            technique_definitions[technique_name] = {
                "protocol_steps": technique.get("protocol_steps", []),
                "checkpoints": technique.get("checkpoints", []),
            }

    return {
        "phases": legacy_phases,
        "technique_definitions": technique_definitions,
        "structured_template": structured_template,
    }
