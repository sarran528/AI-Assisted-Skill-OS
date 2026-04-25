"""Structured skill template retrieval and synthesis pipeline."""

from __future__ import annotations

import hashlib
import json
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

from backend.shared.config import settings

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
From the content provided, extract:
- core concepts and sub-skills
- learning techniques and drills
- common errors and failure modes
- difficulty progression signals

Return ONLY valid JSON. No explanation.

Schema:
{
  "concepts": ["string"],
  "techniques": [{"name": "string", "difficulty": "beginner|intermediate|advanced", "steps": ["string"]}],
  "failure_modes": ["string"],
  "progression_order": ["string"]
}
"""

PASS_2_PROMPT = """
You are a SkillTemplate construction engine.
Convert the extracted concepts into a strict SkillTemplate JSON object.

Rules:
- Return ONLY valid JSON. No preamble. No explanation. No markdown.
- Phases must be exactly: fundamentals, intermediate, advanced, application, mastery
- Each phase: 2-4 techniques maximum
- Each technique: 1-3 checkpoints maximum
- target_metric MUST be quantifiable: time in seconds, accuracy %, count, error rate
- threshold MUST contain a numeric boundary (e.g. ">= 85%", "< 3 errors", "<= 30s")
- Vague metrics like "improve understanding" are INVALID — do not use them
- Techniques must increase in difficulty across phases
- failure_condition must be specific and measurable

Schema:
{
  "skill_id": "string (snake_case)",
  "phases": {
    "<phase_name>": {
      "competencies": ["string"],
      "techniques": [
        {
          "id": "string",
          "name": "string",
          "protocol_steps": ["string"],
          "checkpoints": [
            {
              "id": "string",
              "competency_target": "string",
              "target_metric": "string",
              "threshold": "string",
              "validation_method": "numeric | artifact | behavioral_log",
              "failure_condition": "string"
            }
          ]
        }
      ]
    }
  }
}
"""


def to_skill_id(skill_name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s_-]+", "", skill_name).strip().lower()
    return re.sub(r"[\s-]+", "_", cleaned)


def build_queries(skill_name: str) -> list[str]:
    return [
        f"{skill_name} beginner to advanced learning roadmap",
        f"{skill_name} core techniques and fundamentals",
        f"{skill_name} common mistakes and failure modes",
        f"{skill_name} practice drills and exercises",
        f"{skill_name} skill progression checkpoints",
    ][:MAX_QUERY_COUNT]


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


class SkillTemplatePipeline:
    """Builds schema-enforced skill templates from external web content."""

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=12.0)
        self._cache: dict[str, StructuredTemplateResult] = {}
        self._embedder = self._init_embedder()
        self._faiss_assets = self._init_faiss_assets()

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
            return None

        pass2_payload = f"Skill: {skill_name}\n\nExtracted Data:\n{json.dumps(extracted)}"
        return await self._structured_llm_call(system_prompt=PASS_2_PROMPT, content=pass2_payload, max_tokens=4000)

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
        all_urls: list[str] = []

        for query in queries:
            await self._sleep(query_delay)
            urls = await self._with_backoff(lambda q=query: self.search_web(q, num=query_num))
            all_urls.extend(filter_urls(urls or []))

        raw_texts: list[str] = []
        for url in all_urls[:url_limit]:
            text = await self._with_backoff(lambda u=url: self.extract_text(u))
            if text and len(text) > min_length:
                raw_texts.append(text)

        raw_texts = deduplicate_texts(raw_texts)
        if len(raw_texts) < 2:
            return None

        combined = "\n\n---\n\n".join(raw_texts)
        content_hash = get_content_hash(combined)
        skill_id = to_skill_id(skill_name)

        cached = self._cache.get(skill_id)
        if cached and cached.content_hash == content_hash:
            return cached

        template = await self.structure_template_two_pass(skill_name, combined)
        if template is None:
            return None
        template["skill_id"] = skill_id
        valid, _reason = validate_template(template)
        if not valid:
            return None

        version = hashlib.md5(json.dumps(template, sort_keys=True).encode("utf-8")).hexdigest()[:8]
        result = StructuredTemplateResult(template=template, content_hash=content_hash, version=version)
        self._cache[skill_id] = result
        self._store_in_faiss(result, skill_name)
        return result

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
