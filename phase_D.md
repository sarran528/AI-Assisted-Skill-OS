Phase D — everything needed, in full detail.

---

## Phase D starts with one rule

Phase C must be complete. The Doubt system in step 22 reads current session state to build its query context. The Tip system in step 23 is triggered by session failure conditions and retry counts. Both of those objects — session state and failure records — only exist after Phase C is stable. The RAG data pipeline in step 19 can technically be built earlier, but the runtime retrieval in step 20 and everything above it cannot be properly tested without real session and roadmap data to query against.

---

## Step 19 — RAG data pipeline (offline)

**What it is**

An offline process — not a web server, not a route handler. A script that runs once to index skill knowledge documents, and again whenever new content is added. It reads source documents, splits them into chunks, generates embeddings for each chunk, and stores the chunks and their embeddings in the `rag_chunks` table using pgvector. The runtime retrieval in step 20 queries this table. If this table is empty, retrieval returns nothing.

**New packages**

Add to `requirements.in`: `tiktoken` — OpenAI's tokenizer. Used to count tokens accurately before chunking so chunk sizes are in real tokens, not approximate character counts. Without this, a "512 token chunk" might actually be 700 tokens, which breaks the embedding model's context window. `openai` — the OpenAI Python SDK, used specifically for the `text-embedding-3-small` embedding model. Even if using Anthropic for LLM calls, OpenAI's embedding model is the one specified. `tenacity` is already installed from Phase B. `pypdf2` — for reading PDF source documents. `python-docx` — for reading DOCX source documents. `beautifulsoup4` — for reading HTML source documents. `lxml` — the parser backend for BeautifulSoup.

Add to `requirements-dev.in`: nothing new for this step.

Run `pip-compile --generate-hashes requirements.in`.

**New environment variables**

Add to `settings.py`: `OPENAI_API_KEY: str` — used only for embedding generation, not for LLM calls. `EMBEDDING_MODEL: str = "text-embedding-3-small"`. `EMBEDDING_DIMENSION: int = 1536`. `EMBEDDING_BATCH_SIZE: int = 100` — how many chunks to embed per API call. OpenAI's embedding endpoint accepts up to 2048 inputs per call but 100 is a safe conservative batch size that avoids rate limit issues.

**Folder structure**

```
/scripts
  /rag
    pipeline.py          -- main entry point
    document_loader.py   -- reads source files into raw text
    chunker.py           -- splits text into chunks
    embedder.py          -- calls OpenAI embedding API
    indexer.py           -- writes chunks to pgvector
    validate_index.py    -- verifies index is queryable after build

/data
  /skill_docs
    /drawing
      fundamentals_guide.txt
      gesture_drawing_tutorial.txt
      common_mistakes.txt
    /python-basics
      variables_and_types.txt
      functions_guide.txt
      debugging_guide.txt
```

The `data/skill_docs/` folder is committed to the repository. These are the source documents. They do not need to be rich or long for a college project — 3 to 5 text files per skill, each 500 to 2000 words, is enough to demonstrate real retrieval behavior.

**Files to create**

`scripts/rag/document_loader.py` — reads source documents and returns raw text with metadata attached.

```python
@dataclass
class SourceDocument:
    skill_id: str
    phase: str | None        # None means cross-phase
    technique_id: str | None # None means phase-level
    doc_type: str            # tutorial | technique_guide | failure_analysis | resource
    source_path: str
    content: str
```

`load_documents(skill_docs_dir: str) -> list[SourceDocument]` — walks the directory tree. Convention: `data/skill_docs/{skill_id}/{phase}__{doc_type}.txt`. The double underscore separates the phase slug from the doc type. A file named `fundamentals__technique_guide.txt` in the `drawing/` folder maps to `skill_id="drawing"`, `phase="fundamentals"`, `doc_type="technique_guide"`. A file named `cross_phase__resource.txt` maps to `phase=None`.

Handles three file types: `.txt` files are read directly. `.pdf` files are read via `pypdf2.PdfReader`. `.docx` files are read via `python-docx Document()`. `.html` files are parsed via BeautifulSoup with `lxml` parser, `get_text(separator=" ")` to strip tags. Unsupported extensions are skipped with a logged WARNING.

`scripts/rag/chunker.py` — splits a `SourceDocument` into chunks.

```python
@dataclass
class DocumentChunk:
    skill_id: str
    phase: str | None
    technique_id: str | None
    doc_type: str
    source_path: str
    chunk_index: int
    content: str
    token_count: int
```

`chunk_document(doc: SourceDocument, chunk_size: int = 512, overlap: int = 64) -> list[DocumentChunk]`

Algorithm: initialize `tiktoken.encoding_for_model("text-embedding-3-small")`. Encode the full document content into tokens using `encoding.encode(doc.content)`. Split the token list into chunks of size `chunk_size` with `overlap` tokens of overlap between adjacent chunks. Decode each token slice back to text using `encoding.decode(token_slice)`. This is token-level chunking — not sentence splitting, not paragraph splitting. Token-level chunking guarantees exact chunk sizes and is what the embedding model actually sees.

The overlap: chunk 1 is tokens 0–511. Chunk 2 is tokens 448–959 (starts 64 tokens back). Chunk 3 is tokens 896–1407. This overlap ensures that a concept that spans a chunk boundary appears in full in at least one chunk.

Empty chunks (after decode produces whitespace-only text) are filtered out. Chunks with fewer than 10 tokens are also filtered — they are too short to be useful for retrieval.

`scripts/rag/embedder.py` — calls the OpenAI embedding API.

```python
async def embed_chunks(chunks: list[DocumentChunk]) -> list[tuple[DocumentChunk, list[float]]]:
```

Batches chunks into groups of `EMBEDDING_BATCH_SIZE`. For each batch, calls `openai.AsyncOpenAI().embeddings.create(model="text-embedding-3-small", input=[chunk.content for chunk in batch])`. Extracts the embedding vector from each response item. Returns list of `(chunk, embedding_vector)` pairs. The embedding vector is a list of 1536 floats.

Uses `tenacity` `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))` on the API call. OpenAI's embedding endpoint occasionally returns 429 (rate limit) — retry with backoff handles this transparently.

Validates that each returned embedding has exactly 1536 dimensions. Raises `ValueError` if dimension mismatch — this would mean the model changed and the pgvector column dimension no longer matches.

`scripts/rag/indexer.py` — writes chunks and embeddings to the database.

Uses a synchronous SQLAlchemy session because this is a script, not a web handler. `SyncSessionLocal` from `backend/shared/db/base.py`.

`index_chunks(chunks_with_embeddings: list[tuple[DocumentChunk, list[float]]])` — for each pair, creates a `RagChunk` ORM model instance and bulk-inserts using `session.bulk_save_objects()`. Uses `INSERT ... ON CONFLICT (skill_id, source_path, chunk_index) DO UPDATE SET content = EXCLUDED.content, embedding = EXCLUDED.embedding, model_name = EXCLUDED.model_name` via SQLAlchemy's `insert().on_conflict_do_update()`. This makes the indexer idempotent — running it twice does not create duplicate chunks.

Add a `UNIQUE` constraint on `(skill_id, source_path, chunk_index)` to the `rag_chunks` table. Add this as migration `018_add_rag_chunks_unique.py` if not already in the original `011_create_rag_tables.py` migration.

Before inserting, records the current timestamp in `rag_config.last_indexed_at` and verifies `rag_config.model_name` matches `settings.EMBEDDING_MODEL`. If mismatch, raises an error — changing the embedding model requires a full re-index, and the script refuses to mix embeddings from different models in the same table.

`scripts/rag/pipeline.py` — the main entry point that wires everything together:

```python
async def run_pipeline(skill_docs_dir: str, dry_run: bool = False):
    documents = load_documents(skill_docs_dir)
    print(f"Loaded {len(documents)} documents")
    
    all_chunks = []
    for doc in documents:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    print(f"Generated {len(all_chunks)} chunks")
    
    if dry_run:
        print("Dry run — skipping embedding and indexing")
        return
    
    chunks_with_embeddings = await embed_chunks(all_chunks)
    index_chunks(chunks_with_embeddings)
    print(f"Indexed {len(chunks_with_embeddings)} chunks")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skill-docs-dir", default="data/skill_docs")
    args = parser.parse_args()
    asyncio.run(run_pipeline(args.skill_docs_dir, args.dry_run))
```

Add `make index-rag` to the Makefile: `python scripts/rag/pipeline.py --skill-docs-dir data/skill_docs`.

`scripts/rag/validate_index.py` — runs after indexing to verify the index is functional:

```python
def validate_index():
    with SyncSessionLocal() as db:
        count = db.execute(text("SELECT COUNT(*) FROM rag_chunks")).scalar()
        print(f"Total chunks: {count}")
        
        # test a real vector query
        test_embedding = get_test_embedding("basic drawing technique")
        results = db.execute(
            text("SELECT content FROM rag_chunks ORDER BY embedding <=> :v LIMIT 3"),
            {"v": str(test_embedding)}
        ).fetchall()
        
        print(f"Test query returned {len(results)} results")
        for i, row in enumerate(results):
            print(f"  Result {i+1}: {row.content[:100]}...")
```

Add `make validate-rag` to the Makefile.

**Tests**

`tests/rag/test_chunker.py` — test with a document of exactly 512 tokens produces exactly 1 chunk. Test with 600 tokens produces 2 chunks with 64-token overlap. Test that the second chunk starts at token 448 (512 - 64). Test that chunks with fewer than 10 tokens are filtered. Test that empty string input produces zero chunks. Test token count field matches actual token count via tiktoken.

`tests/rag/test_document_loader.py` — test `.txt` file loads correctly. Test filename parsing: `fundamentals__technique_guide.txt` → correct field mapping. Test `cross_phase__resource.txt` → `phase=None`. Test unsupported extension is skipped with no error raised.

`tests/rag/test_embedder.py` — mock `openai.AsyncOpenAI().embeddings.create`. Test that chunks are batched correctly. Test that retry fires on 429 response. Test that dimension validation raises `ValueError` on 768-dimension response (wrong model). Test that return value has same length as input chunks list.

`tests/rag/test_indexer.py` — integration test using test database. Index 5 chunks. Run indexer again with same 5 chunks (idempotent test) — assert still 5 rows, not 10. Assert `rag_config.last_indexed_at` is updated after run.

---

## Step 20 — RAG runtime retrieval service

**What it is**

The query layer. At runtime, when a user requests resources, submits a doubt, or triggers a tip, this service constructs a context-aware query, generates an embedding for that query, and performs a vector similarity search against `rag_chunks`. Three different query modes exist because the three use cases need different amounts of context and different numbers of results.

**No new packages**

`openai` for embedding the query at runtime — already installed. `asyncpg` and `sqlalchemy` for the vector query — already installed.

**Files to create**

`backend/rag/` — new feature folder. Add `__init__.py`.

`backend/rag/embedder.py` — runtime embedding function. Different from the offline embedder in scripts — this one embeds a single query string synchronously (or async) at request time.

```python
async def embed_query(query_text: str) -> list[float]:
```

Calls `openai.AsyncOpenAI().embeddings.create(model=settings.EMBEDDING_MODEL, input=[query_text])`. Returns the 1536-float vector. Uses `@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))` — one retry on failure. If both fail, raises `SystemError("embedding_failed")` which returns a 503 to the client.

The query embedding is not cached — queries are too varied and caching embeddings by query string is fragile. The embedding call takes approximately 50–150ms which is acceptable for the support systems.

`backend/rag/retriever.py` — the core retrieval logic.

```python
@dataclass
class RetrievalQuery:
    query_text: str
    skill_id: str
    phase: str | None
    technique_id: str | None
    doc_type_filter: list[str] | None  # None means all doc types
    top_k: int

@dataclass  
class RetrievedChunk:
    chunk_id: UUID
    skill_id: str
    phase: str | None
    technique_id: str | None
    doc_type: str
    content: str
    similarity_score: float  # cosine similarity 0-1
```

`retrieve(db: AsyncSession, query: RetrievalQuery) -> list[RetrievedChunk]`

Step 1: embed the `query_text` using `embed_query()`.

Step 2: build the SQL query. pgvector's cosine similarity operator is `<=>`. The query uses a pre-filter on metadata columns before the vector search — this is critical for performance and relevance. Without pre-filtering, the vector search returns chunks from any skill which pollutes results:

```python
from sqlalchemy import text

sql = text("""
    SELECT 
        id, skill_id, phase, technique_id, doc_type, content,
        1 - (embedding <=> :query_embedding) AS similarity_score
    FROM rag_chunks
    WHERE skill_id = :skill_id
      AND (:phase IS NULL OR phase = :phase OR phase IS NULL)
      AND (:technique_id IS NULL OR technique_id = :technique_id OR technique_id IS NULL)
      AND (:doc_type_filter IS NULL OR doc_type = ANY(:doc_type_filter))
    ORDER BY embedding <=> :query_embedding
    LIMIT :top_k
""")
```

The `embedding <=> :query_embedding` parameter must be passed as a string in pgvector format: `"[0.123, 0.456, ...]"`. Format the list as: `"[" + ",".join(str(f) for f in embedding_vector) + "]"`.

Step 3: execute query, map results to `RetrievedChunk` dataclass list, return.

Step 4: filter results by minimum similarity score threshold: `similarity_score >= 0.70`. Chunks below this threshold are not useful — they were returned only because the query demanded `top_k` results. If fewer than the minimum useful results remain after filtering, log a WARNING.

`backend/rag/query_builder.py` — constructs `RetrievalQuery` objects for each of the three use cases. This file encodes the retrieval strategy differences between resource, doubt, and tip queries.

```python
def build_resource_query(skill_id: str, phase: str, user_query: str | None) -> RetrievalQuery:
    query_text = f"learning resources for {skill_id} {phase}"
    if user_query:
        query_text = user_query + f" {skill_id} {phase}"
    return RetrievalQuery(
        query_text=query_text,
        skill_id=skill_id,
        phase=phase,
        technique_id=None,
        doc_type_filter=["tutorial", "resource"],
        top_k=5
    )

def build_doubt_query(skill_id: str, phase: str, technique_id: str, user_question: str) -> RetrievalQuery:
    query_text = f"{user_question} {skill_id} {phase} {technique_id}"
    return RetrievalQuery(
        query_text=query_text,
        skill_id=skill_id,
        phase=phase,
        technique_id=technique_id,
        doc_type_filter=None,   # search all doc types for doubts
        top_k=7
    )

def build_tip_query(skill_id: str, technique_id: str, failure_type: str) -> RetrievalQuery:
    query_text = f"correction hint {technique_id} {failure_type} common mistake fix"
    return RetrievalQuery(
        query_text=query_text,
        skill_id=skill_id,
        phase=None,
        technique_id=technique_id,
        doc_type_filter=["failure_analysis", "technique_guide"],
        top_k=3
    )
```

`backend/rag/context_builder.py` — takes retrieved chunks and formats them into a context string for LLM prompt injection.

```python
def build_context_string(chunks: list[RetrievedChunk], max_tokens: int = 2000) -> str:
```

Concatenates chunk contents with separators. Respects a token budget — stops adding chunks when accumulated token count would exceed `max_tokens`. Uses tiktoken to count. Orders chunks by `similarity_score` descending so highest-relevance content is closest to the top of the context. Returns the formatted string.

Format:
```
[Source: drawing / fundamentals / technique_guide]
Blind contour drawing is a foundational technique...

[Source: drawing / fundamentals / failure_analysis]  
Common mistake: lifting the pen...
```

**Tests**

`tests/rag/test_retriever.py` — requires the test database to have indexed chunks. Use a fixture that inserts 10 known chunks with known embeddings. Mock `embed_query` to return a known vector. Assert that retrieval returns the most similar chunks first. Assert that pre-filtering by `skill_id` excludes chunks from other skills. Assert that chunks with `similarity_score < 0.70` are filtered out. Assert `top_k` limits the result count.

`tests/rag/test_query_builder.py` — test `build_resource_query` produces `top_k=5` and `doc_type_filter=["tutorial", "resource"]`. Test `build_doubt_query` produces `top_k=7` and `doc_type_filter=None`. Test `build_tip_query` produces `top_k=3` and `doc_type_filter=["failure_analysis", "technique_guide"]`. Test that `user_question` is incorporated into the query text for doubt queries.

`tests/rag/test_context_builder.py` — test that chunks are ordered by similarity score descending. Test that `max_tokens` budget is respected — a list of 7 chunks that would exceed 2000 tokens is truncated. Test the output format contains the source metadata headers.

---

## Step 21 — Resource system

**What it is**

Returns curated learning resources for the current phase and technique. Triggered either automatically when a user enters a new phase or manually when the user requests them. Display only — reading resources never updates session state, never marks progress, never unlocks anything.

**No new packages**

All needed: `openai` for embeddings, `sqlalchemy` for DB, FastAPI already installed.

**Files to create**

`backend/support/` — new feature folder for all three support systems. Add `__init__.py`.

`backend/support/resource_service.py`

```python
async def get_resources(
    db: AsyncSession,
    skill_id: str,
    phase: str,
    user_query: str | None,
    current_user: User
) -> ResourceResponse:
```

Calls `build_resource_query()` from `query_builder.py`. Calls `retrieve()` from `retriever.py`. If fewer than 2 chunks returned, logs a WARNING — index may be incomplete for this skill/phase. Calls `build_context_string()` to format retrieved chunks. Does NOT call the LLM — resources are returned as raw retrieved content, not LLM-generated text. The retrieved chunk content is the resource. Returns a structured list of resource items.

```python
@dataclass
class ResourceItem:
    title: str           # derived from first line of chunk or doc_type label
    content: str         # the chunk content
    doc_type: str
    phase: str | None
    relevance_score: float
    
@dataclass
class ResourceResponse:
    skill_id: str
    phase: str
    resources: list[ResourceItem]
    query_used: str
```

This is important: resources do not go through the LLM. RAG retrieval is sufficient. The LLM adds latency and cost without meaningful benefit for resource listing — the raw chunk content is already useful text.

`backend/support/schemas.py` — Pydantic versions of `ResourceItem` and `ResourceResponse` for API output. Also `ResourceRequest` with `skill_id: str`, `phase: str`, `user_query: str | None`.

`backend/support/router.py` — `GET /resources` with query parameters `skill_id`, `phase`, `user_query` (optional). Returns `ResourceResponse`. Requires auth. No job queue — fast enough to run synchronously. Embedding takes ~100ms, vector query takes ~20ms, total under 200ms.

Add a route trigger hook in `backend/roadmap/service.py`: after `transition_roadmap_phase()` sets a new phase to `active`, enqueue a background task that pre-fetches resources for that phase and caches them in Redis with key `resources:{user_id}:{skill_id}:{phase}`, TTL 1 hour. This makes the first resource request instant. The background task is a new Celery task: `prefetch_resources_task(user_id, skill_id, phase)`. Add it to `backend/shared/queue/tasks.py`.

Redis caching for resources: in `resource_service.py`, before calling retriever, check Redis for `resources:{skill_id}:{phase}:{hash(user_query)}`. If hit, deserialize and return immediately. If miss, compute and store. TTL 30 minutes for user-query-specific results, 60 minutes for phase-level results.

**Tests**

`tests/support/test_resource_service.py` — mock `retrieve()` to return 5 known chunks. Assert `ResourceResponse` contains 5 items. Assert LLM is never called — use `unittest.mock.patch` on the LLM gateway and assert it was never invoked. Test with `user_query=None` uses phase-level query. Test with `user_query="how to hold a pencil"` incorporates the query. Test Redis cache hit returns immediately without calling `retrieve()`. Test that `relevance_score` field matches the `similarity_score` from retrieved chunks.

---

## Step 22 — Doubt system

**What it is**

The user submits a natural language question during a session. The system retrieves relevant chunks from the RAG index using the question plus session context, then passes those chunks to the LLM to generate a grounded, specific answer. The answer never changes session state, never marks progress, never affects the validation engine. It is purely informational.

**No new packages**

LLM gateway from step 10, RAG retriever from step 20 — both already installed.

**Files to create**

`backend/support/doubt_service.py`

```python
async def answer_doubt(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    user_question: str,
    current_user: User
) -> DoubtResponse:
```

Step 1: fetch the current session to extract `skill_id`, `phase`, `technique_id`. If no active session exists for the user, allow the doubt anyway but with only `skill_id` context — a user might ask a question between sessions.

Step 2: call `build_doubt_query(skill_id, phase, technique_id, user_question)`.

Step 3: call `retrieve(db, doubt_query)` — gets top 7 most relevant chunks.

Step 4: call `build_context_string(chunks, max_tokens=2000)`.

Step 5: build the LLM prompt using a function in `backend/shared/llm/prompts.py`:

```python
def build_doubt_prompt(context: str, question: str, skill_id: str, phase: str, technique: str) -> str:
    return f"""You are a learning assistant for the skill: {skill_id}.
The learner is currently in the {phase} phase, working on: {technique}.

Use ONLY the following reference material to answer the question.
Do not use any knowledge outside of the provided context.
If the context does not contain enough information to answer, say so clearly.

CONTEXT:
{context}

QUESTION:
{question}

Respond with a concise, specific answer in 2-4 sentences. No preamble."""
```

Step 6: call `llm_call()` with this prompt. Use `temperature=0.2` for doubt — slightly relaxed from 0.0 because natural language explanation benefits from slight variation. Define a `DoubtAnswerSchema`:

```python
class DoubtAnswerSchema(BaseModel):
    answer: str
    source_phases: list[str]  # which phases the answer drew from
    confidence: Literal["high", "medium", "low"]
    caveat: str | None        # if context was insufficient
```

Step 7: persist the doubt and answer in a `doubt_log` table for analytics and audit. This table is not used for retrieval — it is append-only.

Step 8: write audit log `doubt.submitted`.

Step 9: return `DoubtResponse`.

```python
@dataclass
class DoubtResponse:
    question: str
    answer: str
    confidence: str
    caveat: str | None
    chunks_used: int
    session_context: dict  # skill_id, phase, technique — for frontend display
```

**New DB table: doubt_log**

Add migration `019_create_doubt_log.py` with columns: `id UUID PK`, `user_id UUID FK`, `session_id UUID FK NULLABLE`, `skill_id VARCHAR(64)`, `phase VARCHAR(64) NULLABLE`, `question TEXT NOT NULL`, `answer TEXT NOT NULL`, `chunks_used INT`, `confidence VARCHAR(16)`, `created_at TIMESTAMPTZ`.

`backend/shared/db/repositories/doubt_repository.py` — `create(session, data) -> DoubtLogModel`.

`backend/support/router.py` additions — `POST /doubt/ask` with body `{ session_id: UUID | None, user_question: str }`. Returns `DoubtResponse`. Requires auth. Rate limited to 10 requests per minute per user via SlowAPI — add to `backend/auth/middleware.py` rate limit config.

Add to `backend/shared/llm/schemas.py`:
```python
class DoubtAnswerSchema(BaseModel):
    answer: str
    source_phases: list[str]
    confidence: Literal["high", "medium", "low"]
    caveat: str | None = None
```

Fallback for doubt LLM call: `DoubtAnswerSchema(answer="Unable to generate an explanation at this time. Please consult the provided resources.", source_phases=[], confidence="low", caveat="LLM unavailable")`. The fallback is honest and useful — it tells the user to use the resource system instead.

**Input validation**

`user_question` must be between 10 and 500 characters. Enforced in the Pydantic request schema with `min_length=10, max_length=500`. Questions shorter than 10 characters are likely accidental. Questions longer than 500 characters are likely copy-pasted text rather than actual questions.

**Tests**

`tests/support/test_doubt_service.py` — mock `retrieve()` to return 5 chunks. Mock `llm_call()` to return valid `DoubtAnswerSchema`. Assert answer is returned. Assert `doubt_log` record created in test DB. Assert LLM is called with `temperature=0.2`. Assert LLM prompt contains the retrieved context. Test with no active session — doubt still works with skill-level context. Test LLM fallback: mock `llm_call()` to return invalid JSON both times, assert `DoubtResponse.answer` contains the fallback message. Test rate limit: submit 11 requests in quick succession, assert 11th returns 429. Test question shorter than 10 characters returns 422 from Pydantic validation.

---

## Step 23 — Tip system

**What it is**

Triggered automatically by failure conditions — repeated session failures, high retry count, or high performance decay. Returns a specific, actionable correction hint targeted at what the learner is doing wrong. Not a general explanation like the doubt system. Not a resource list. A single focused correction. "You are pressing too hard when drawing lines — reduce pressure and slow down." That specificity is the point.

**No new packages**

Everything installed.

**Trigger conditions**

The tip system is triggered in three situations defined in the session execution engine from Phase C. Add trigger detection to `backend/session/service.py` in the `complete_session()` function — after the session result is determined:

Condition 1 — Repeated failure: `session.attempt_number >= 2` and `session_result.passed == False`. The learner has now failed the same technique at least twice.

Condition 2 — High retry count: `session.metrics_captured["retry_count"] > params.retry_limit`. The learner exhausted retries within a single session.

Condition 3 — High decay: if `session.metrics_captured` contains a `performance_decay` value and `performance_decay > 0.5`. The learner started well but degraded significantly during the session.

When any condition is met, `complete_session()` calls `generate_tip()` from `tip_service.py` asynchronously — it enqueues a Celery task `generate_tip_task(session_id, technique_id, failure_reason)`. The tip is generated in the background and stored. The session complete response includes `{ tip_pending: true, tip_poll_url: "/tip/{session_id}" }` so the frontend knows to poll.

**Files to create**

`backend/support/tip_service.py`

```python
async def generate_tip(
    db: AsyncSession,
    session_id: UUID,
    skill_id: str,
    technique_id: str,
    failure_reason: str,
    session_metrics: dict,
    params: LearningParameters
) -> TipResponse:
```

Step 1: determine the `failure_type` string — more specific than `failure_reason`. Map:
- `failure_reason="protocol_violation"` + which step failed → `failure_type="step_{step_id}_skipped"`
- `failure_reason="metric_threshold"` + low accuracy → `failure_type="accuracy_below_threshold"`
- `failure_reason="metric_threshold"` + high error count → `failure_type="excessive_errors"`
- `failure_reason="incomplete_execution"` → `failure_type="session_not_completed"`
- high decay → `failure_type="performance_degradation"`

Step 2: call `build_tip_query(skill_id, technique_id, failure_type)` — top 3 chunks, filtered to `failure_analysis` and `technique_guide` doc types.

Step 3: call `retrieve(db, tip_query)`.

Step 4: build LLM prompt from `backend/shared/llm/prompts.py`:

```python
def build_tip_prompt(context: str, technique_id: str, failure_type: str, attempt_number: int) -> str:
    return f"""You are providing a targeted correction for a learner who is failing at: {technique_id}.
Failure type: {failure_type}
Number of failed attempts: {attempt_number}

Use ONLY the following reference material.
Provide ONE specific, actionable correction. Maximum 2 sentences.
Do not explain why this matters. Do not provide encouragement. Just the correction.

CONTEXT:
{context}

Tip:"""
```

The prompt is deliberately terse. The LLM must produce a short correction, not an essay.

Step 5: define `TipSchema`:

```python
class TipSchema(BaseModel):
    tip: str              # the correction — max 100 words enforced by validator
    target_step: str | None  # which protocol step this tip addresses
    severity: Literal["minor", "moderate", "critical"]
    
    @validator("tip")
    def tip_max_words(cls, v):
        if len(v.split()) > 100:
            raise ValueError("tip must be 100 words or fewer")
        return v
```

Step 6: call `llm_call()` with `temperature=0.0`. Tips must be deterministic — a given failure pattern should produce the same correction every time.

Step 7: persist in `tip_log` table.

Step 8: write audit log `tip.generated`.

Step 9: return `TipResponse`.

```python
@dataclass
class TipResponse:
    session_id: UUID
    technique_id: str
    tip: str
    severity: str
    target_step: str | None
    failure_type: str
    generated_at: datetime
```

**Fallback for tip LLM**

`TipSchema(tip="Focus on completing each step in the protocol before moving to the next. Do not skip steps.", target_step=None, severity="moderate")`. The fallback is generic but still actionable — not an error message.

**New DB table: tip_log**

Add migration `020_create_tip_log.py` with columns: `id UUID PK`, `session_id UUID FK`, `user_id UUID FK`, `technique_id VARCHAR(64)`, `failure_type VARCHAR(64)`, `attempt_number INT`, `tip TEXT`, `severity VARCHAR(16)`, `target_step VARCHAR(64) NULLABLE`, `chunks_used INT`, `created_at TIMESTAMPTZ`.

`backend/shared/db/repositories/tip_repository.py` — `create(session, data) -> TipLogModel`, `get_latest_for_session(session, session_id) -> TipLogModel | None`.

**New Celery task**

In `backend/shared/queue/tasks.py`:

```python
@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def generate_tip_task(self, session_id: str, skill_id: str, technique_id: str, 
                       failure_reason: str, session_metrics: dict, params_id: str):
    try:
        with SyncSessionLocal() as db:
            params = sync_get_learning_parameters(db, UUID(params_id))
            result = sync_generate_tip(db, UUID(session_id), skill_id, 
                                        technique_id, failure_reason, session_metrics, params)
            return {"tip": result.tip, "severity": result.severity}
    except Exception as exc:
        raise self.retry(exc=exc)
```

`sync_generate_tip()` is the synchronous version of `generate_tip()` using `SyncSessionLocal`.

**Router additions**

`backend/support/router.py`: `GET /tip/:session_id` — returns the latest tip for a session if available, or `{ tip_pending: true }` if the Celery task has not yet completed. Checks `tip_log` table first, then falls back to checking the Celery job status via `AsyncResult`.

**Trigger integration in session service**

Update `backend/session/service.py` `complete_session()` to check all three trigger conditions after computing `session_result`. If any condition is met:

```python
if should_generate_tip(session_result, session, params):
    generate_tip_task.delay(
        str(session_id),
        skill_id,
        session.technique_id,
        session_result.failure_reason,
        session.metrics_captured,
        str(params.id)
    )
    tip_pending = True
else:
    tip_pending = False
```

Add `tip_pending: bool` to the `SessionCompleteResponse` schema.

`should_generate_tip(result, session, params) -> bool` is a pure function in `backend/session/execution.py`:

```python
def should_generate_tip(
    result: SessionResult,
    session: SessionModel,
    params: LearningParameters
) -> bool:
    if result.passed:
        return False
    if session.attempt_number >= 2:
        return True
    metrics = session.metrics_captured
    if metrics.get("retry_count", 0) > params.retry_limit:
        return True
    if metrics.get("performance_decay", 0) > 0.5:
        return True
    return False
```

**Tests**

`tests/support/test_tip_service.py` — mock `retrieve()` and `llm_call()`. Test tip generated when `attempt_number=2` and session failed. Test tip NOT generated when `attempt_number=1` and session failed — only one failure is not enough. Test tip NOT generated when session passed — passing sessions never get tips. Test `should_generate_tip()` with each trigger condition independently. Test high retry count triggers tip. Test high decay triggers tip. Test that LLM is called with `temperature=0.0`. Test tip Pydantic validator rejects tips longer than 100 words. Test fallback tip is returned when LLM fails both attempts. Test that `tip_log` record is created in test DB. Test `GET /tip/:session_id` returns `tip_pending=true` when Celery task not yet complete, returns full tip when complete.

---

## Phase D completion gate

Phase D is complete when all of the following are true.

✅ `tests/rag/`, `tests/support/` all pass with zero failures.

✅ `make index-rag` runs successfully and `make validate-rag` confirms at least 20 chunks indexed across at least 2 skills.

✅ `make validate-rag` test query returns at least 2 results — the HNSW index is functional.

✅ `GET /resources?skill_id=drawing&phase=fundamentals` returns at least 3 resource items with `relevance_score > 0.70`.

✅ `POST /doubt/ask` with a valid session context returns a grounded answer that references content from the indexed chunks — not a generic response.

✅ `GET /tip/:session_id` after a second session failure returns a specific tip with `severity` field populated.

✅ The tip is NOT generated after a first failure — `should_generate_tip()` returns False for `attempt_number=1`.

✅ Celery task `generate_tip_task` completes successfully in the `task_always_eager` test mode.

✅ Redis caching for resources is verified — second call to `GET /resources` with identical parameters does not call `embed_query()` — mock confirms zero calls on cache hit.

✅ Migrations 018 through 020 all have working `downgrade()` functions tested against the test database.

✅ `POST /doubt/ask` with `user_question` of 9 characters returns 422 validation error.

✅ `POST /doubt/ask` called 11 times rapidly returns 429 on the 11th call.

✅ LLM is never called by the resource system — verified in `test_resource_service.py` with mock assertion.