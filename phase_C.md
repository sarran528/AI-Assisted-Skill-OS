Phase C — everything needed, in full detail.

---

## Phase C starts with one rule

Phase B must be complete. The roadmap generator in step 13 takes a `SkillResearchObject` and a `SkillTemplate` as inputs — both produced in Phase B. The session execution engine in step 14 takes a roadmap as input — produced in step 13. Every step in Phase C has a hard dependency on the step before it. No step can be started until the previous one is tested and stable.

---

## Step 13 — Roadmap generation engine

**What it is**

Takes the `SkillResearchObject` from step 11 and the `SkillTemplate` from step 8 and produces a fully specified, deterministic roadmap. Given identical inputs, it must always produce identical output. The output is hashed and the hash is stored alongside the roadmap so integrity can be verified at any time.

**New packages**

Add to `requirements.in`: `hashlib` is already in Python standard library — no install needed. `json` is standard library. No new pip packages needed for the core generation. However you need `canonicaljson` — add it. This is a library that serializes Python dicts to canonical JSON with sorted keys and no whitespace variation. Standard `json.dumps(sort_keys=True)` is close but `canonicaljson` guarantees byte-for-byte identical output across Python versions and platforms, which is what determinism actually requires.

Run `pip-compile --generate-hashes requirements.in` again.

**Files to create**

`backend/roadmap/` — new feature folder. Add `__init__.py`.

`backend/roadmap/generator.py` — the core generation file. Everything deterministic lives here. No LLM calls. No DB calls. Pure computation that takes typed inputs and returns a typed output.

Define `GeneratedRoadmap` as a Pydantic model:

```python
class GeneratedRoadmap(BaseModel):
    skill_id: str
    user_id: UUID
    profile_version: int
    template_version: int
    parameters_id: UUID
    phases: dict[str, RoadmapPhase]
    total_estimated_weeks: int
    fingerprint: str  # SHA-256 of canonical serialization
    generated_at: datetime

class RoadmapPhase(BaseModel):
    phase_slug: str
    competencies: list[str]
    techniques: list[RoadmapTechnique]
    checkpoints: list[RoadmapCheckpoint]
    estimated_weeks: int
    status: Literal["locked", "active", "completed"] = "locked"

class RoadmapTechnique(BaseModel):
    technique_id: str
    name: str
    session_count: int       # how many sessions to complete this technique
    protocol_steps: list[str]

class RoadmapCheckpoint(BaseModel):
    checkpoint_id: str
    description: str
    evidence_type: Literal["numeric", "artifact", "behavioral_log"]
    threshold: float         # derived from validation_strictness parameter
    pass_criteria: str
```

`generate_roadmap(research: SkillResearchObject, template: SkillTemplate, params: LearningParameters) -> GeneratedRoadmap` — the main function. Algorithm:

For each phase in the template's `structure.phases`:
- Filter competencies: if `research.feasibility.risk_level == "high"` and the template has more than 3 competencies in this phase, take only the top 3 ordered by their position in the template list. This is the feasibility filter.
- Select techniques: take `floor(params.technique_density * len(available_techniques))` techniques from the phase, minimum 1. Sort the available techniques alphabetically before selecting — this ensures determinism regardless of dict ordering.
- Assign session count per technique: `max(1, round(params.repetition_intensity * 3))`. So low `repetition_intensity` gives 1 session per technique, high gives 3.
- Build `protocol_steps` for each technique: these are fetched from the skill template's technique definitions. If the template does not define protocol steps for a technique, generate a default list: `["Set up materials", "Execute technique", "Review output", "Record observations"]`.
- Build checkpoints: for each checkpoint string in the template phase, create a `RoadmapCheckpoint`. Set `threshold = params.checkpoint_rigidity`. Set `evidence_type` based on a rule: if the checkpoint string contains "produce", "draw", "create", "record", "write" → `artifact`. If it contains "accuracy", "score", "percentage", "within" → `numeric`. Otherwise → `behavioral_log`.
- Set `estimated_weeks` for each phase: read from `research.time_model.hours_per_phase` if the phase slug exists there, else default to 2 weeks.

After all phases are built, set the first phase `status = "active"`, all others `status = "locked"`.

Serialize the full roadmap to canonical JSON using `canonicaljson.encode_canonical_json()`. SHA-256 hash the bytes. Store as hex string in `fingerprint`.

**Determinism verification function**

```python
def verify_roadmap_integrity(roadmap: GeneratedRoadmap) -> bool:
    serialized = canonicaljson.encode_canonical_json(
        roadmap.model_dump(exclude={"fingerprint", "generated_at"})
    )
    expected = hashlib.sha256(serialized).hexdigest()
    return roadmap.fingerprint == expected
```

This function is called in the validation engine and in tests. `generated_at` is excluded from the hash because it is a timestamp that changes per generation but does not affect content.

`backend/roadmap/service.py` — `create_roadmap(db, user_id, skill_id) -> GeneratedRoadmap`. Fetches the latest `SkillResearchObject` for this user+skill (raises `BusinessError("research_required")` if none). Fetches active skill template. Fetches the skill-adjusted `LearningParameters` for this user+skill. Calls `generate_roadmap()`. Verifies integrity with `verify_roadmap_integrity()`. Persists via repository. Writes audit log `roadmap.generated`. Returns the object.

`backend/shared/db/repositories/roadmap_repository.py` — `create(session, roadmap: GeneratedRoadmap, user_id, parameters_id) -> RoadmapModel`, `get_active(session, user_id, skill_id) -> RoadmapModel | None`, `get_by_id(session, roadmap_id) -> RoadmapModel | None`, `update_status(session, roadmap_id, status)`, `get_phase_status(session, roadmap_id, phase_slug) -> str`, `advance_phase(session, roadmap_id, current_phase_slug)` — sets current phase to `completed`, sets next phase to `active`.

`backend/roadmap/router.py` — `POST /roadmap/generate` returns `202 { job_id }` once the job queue is added in step 18. For now in Phase C it runs synchronously and returns `201 { roadmap_id }`. `GET /roadmap/:user_id` returns the active roadmap serialized. `GET /roadmap/:roadmap_id/verify` calls `verify_roadmap_integrity()` and returns `{ valid: bool, fingerprint: str }`.

`backend/roadmap/schemas.py` — `RoadmapGenerateRequest` with `skill_id: str`. `RoadmapResponse` mapping the ORM model to camelCase output. `RoadmapVerifyResponse`.

Add migration `014_create_roadmaps.py` — this was described in Phase A schema but the actual Alembic file is written now since the ORM model now exists.

**Tests**

`tests/roadmap/test_generator.py` — the most important test file in Phase C.

Determinism test: call `generate_roadmap()` twice with identical inputs, assert `roadmap1.model_dump() == roadmap2.model_dump()` field by field including `fingerprint`. This is the primary regression test.

Fingerprint test: call `verify_roadmap_integrity(roadmap)` and assert `True`. Then mutate one field in the roadmap dict and call verify again, assert `False`.

Feasibility filter test: provide a `SkillResearchObject` with `risk_level="high"` and a template phase with 5 competencies. Assert the generated phase has exactly 3 competencies.

Technique selection test: provide `technique_density=0.5` and a phase with 4 techniques. Assert exactly 2 techniques are selected. Test with `technique_density=0.0` and assert exactly 1 technique is selected (minimum 1 enforced).

Session count test: `repetition_intensity=0.0` → `session_count=1`, `repetition_intensity=0.5` → `session_count=2`, `repetition_intensity=1.0` → `session_count=3`.

Evidence type assignment test: checkpoint string "produce 5 shapes" → `artifact`. "achieve 90% accuracy" → `numeric`. "complete all protocol steps" → `behavioral_log`.

Phase ordering test: assert that exactly one phase has `status="active"` in the generated roadmap, it is the first phase, all others are `"locked"`.

---

## Step 14 — Session execution engine

**What it is**

Controls the runtime of a single technique practice session. The user performs a technique protocol step by step. The system captures metrics in real time, checks that protocol steps were not skipped, stores evidence, and produces a pass or fail ruling. A session that fails does not advance progress. Period.

**New packages**

No new packages. Everything is in place from Phases A and B.

**Files to create**

`backend/session/` — new feature folder. Add `__init__.py`.

`backend/session/execution.py` — the core protocol execution logic. Pure functions, no DB.

Define `SessionMetrics` as a dataclass:

```python
@dataclass
class SessionMetrics:
    accuracy_pct: float | None
    time_taken_seconds: float | None
    error_count: int | None
    step_completion_rate: float   # completed_steps / total_steps
    retry_count: int
    raw_signals: dict             # everything captured, for auditability
```

`validate_protocol_adherence(completed_steps: list[str], required_steps: list[str]) -> tuple[bool, list[str]]` — checks that every required step ID appears in `completed_steps` in order. Returns `(True, [])` if all steps present in order, `(False, [missing_step_ids])` if any are missing or out of order. This is what enforces "no step skipping".

`compute_session_result(metrics: SessionMetrics, params: LearningParameters, adherence_ok: bool) -> SessionResult` — takes the captured metrics and determines pass or fail. Returns a `SessionResult` dataclass with `passed: bool`, `failure_reason: str | None`, `metric_details: dict`.

`SessionResult` failure conditions: if `adherence_ok == False` → `failure_reason = "protocol_violation"`. If `metrics.accuracy_pct` is not None and `metrics.accuracy_pct < params.error_tolerance_threshold` → `failure_reason = "metric_threshold"`. If `metrics.step_completion_rate < 1.0` → `failure_reason = "incomplete_execution"`. If none of the above → `passed = True`.

`backend/session/service.py` — the service layer. Four functions:

`start_session(db, user_id, roadmap_id, phase, technique_id) -> UUID` — creates a session row with `status="pending"`, verifies the roadmap is active and the phase is active (raises `BusinessError("phase_not_active")` if not), transitions session to `status="active"`, writes audit log `session.started`, returns `session_id`.

`submit_metrics(db, session_id, metrics_payload: dict)` — appends incoming metrics to `sessions.metrics_captured` JSONB. This is called multiple times during a session as metrics stream in. Uses PostgreSQL's `jsonb_set` or a Python-side merge to accumulate. Does not change session status.

`complete_session(db, redis, session_id, completed_steps: list[str]) -> SessionResult` — fetches the session, fetches the roadmap phase to get required steps, fetches learning parameters for adherence thresholds, calls `validate_protocol_adherence()`, calls `compute_session_result()`, transitions session to `status="completed"` or `status="failed"` via the orchestration layer (not directly — see step 17), writes audit log `session.completed` or `session.failed`, returns `SessionResult`.

`get_session_status(db, session_id) -> dict` — returns current session state for polling.

`backend/session/schemas.py` — `SessionStartRequest` with `roadmap_id: UUID`, `phase: str`, `technique_id: str`. `SessionMetricsRequest` with `metrics: dict`. `SessionCompleteRequest` with `completed_steps: list[str]`. `SessionResponse` with full session state.

`backend/session/router.py` — four routes: `POST /session/start` → calls `start_session`, returns `{ session_id }`. `POST /session/metrics` → calls `submit_metrics`, returns `{ acknowledged: true }`. `POST /session/complete` → calls `complete_session`, returns `SessionResult` serialized. `GET /session/:session_id` → returns current session state.

All four routes require auth. `POST /session/metrics` is designed to be called frequently during a session — it must be fast. It does a single JSONB update to the session row and returns immediately. No heavy processing.

`backend/shared/db/repositories/session_repository.py` — `create(session, data) -> SessionModel`, `get_by_id(session, session_id) -> SessionModel | None`, `append_metrics(session, session_id, metrics: dict)`, `update_status(session, session_id, status: str, failure_reason: str | None)`, `get_active_session(session, user_id) -> SessionModel | None` — returns the single active session for a user if one exists, `set_completed_steps(session, session_id, steps: list[str])`.

Add migration `015_create_sessions.py`.

**Tests**

`tests/session/test_execution.py`

Protocol adherence test: required steps `["s1","s2","s3"]`, completed `["s1","s2","s3"]` → `(True, [])`. Completed `["s1","s3"]` → `(False, ["s2"])`. Completed `["s2","s1","s3"]` (wrong order) → `(False, ["s1"])`. Completed `["s1","s2"]` → `(False, ["s3"])`.

Session result test: adherence failed → `passed=False, failure_reason="protocol_violation"`. Adherence ok but accuracy below threshold → `passed=False, failure_reason="metric_threshold"`. Adherence ok, accuracy ok → `passed=True`.

Integration test using test DB: start session, submit metrics three times, complete session with all steps, assert session row is `status="completed"`. Start session, complete with missing step, assert session row is `status="failed"` with `failure_reason="protocol_violation"`.

Concurrent session test: attempt to start a second session while one is active for the same user, assert `BusinessError` is raised.

---

## Step 15 — Evidence upload pipeline

**What it is**

Handles multipart file upload from the client, stores the file in S3 or Cloudflare R2, and creates the evidence metadata record in the database. The file and its metadata are linked to a specific session and checkpoint. Without valid evidence attached to a checkpoint, that checkpoint cannot pass — the validation engine in step 16 will reject it.

**New packages**

Add to `requirements.in`: `boto3` — the AWS SDK for Python, used for both S3 and Cloudflare R2 (R2 is S3-compatible). `python-magic` — detects actual file MIME type from file bytes, not from the file extension sent by the client. Extension-based MIME detection is a security vulnerability. `python-magic` reads the file header bytes. On Linux this requires `libmagic1` to be installed in the Docker container — add `RUN apt-get install -y libmagic1` to your `Dockerfile`.

Also add `aioboto3` — the async wrapper around boto3, needed because your FastAPI handlers are async and blocking boto3 calls inside async functions will block the event loop.

Run `pip-compile --generate-hashes requirements.in`.

**New environment variables**

Add to `settings.py`: `S3_BUCKET_NAME: str`, `S3_REGION: str`, `S3_ACCESS_KEY_ID: str`, `S3_SECRET_ACCESS_KEY: str`, `S3_ENDPOINT_URL: str | None = None` — this is set to the R2 endpoint if using Cloudflare R2, left as None for standard AWS S3. This single setting lets you switch between S3 and R2 without changing any code.

**Files to create**

`backend/shared/storage/s3_client.py` — creates and caches the `aioboto3` session and S3 client. `get_s3_client()` returns an async context manager wrapping the S3 client configured with the environment variables. If `S3_ENDPOINT_URL` is set, passes it as `endpoint_url` to the client — this is the R2 switch.

`backend/shared/storage/uploader.py` — the upload logic:

```python
async def upload_evidence_file(
    file_bytes: bytes,
    original_filename: str,
    session_id: UUID,
    checkpoint_id: str,
    user_id: UUID
) -> tuple[str, str, str]:  # returns (object_key, artifact_url, detected_mime_type)
```

Generates the S3 object key as `evidence/{user_id}/{session_id}/{checkpoint_id}/{uuid4()}/{original_filename}`. Detects MIME type using `python-magic.from_buffer(file_bytes, mime=True)`. Validates MIME type is in the allowed set: `{"image/png", "image/jpeg", "image/gif", "image/webp", "application/pdf", "text/plain", "video/mp4"}`. Raises `BusinessError("unsupported_mime_type")` if not in set. Validates file size: `len(file_bytes) <= 52_428_800` (50MB). Raises `BusinessError("file_too_large")` if exceeded. Calls `s3_client.put_object()` with the bytes, key, content type. Returns the key, a presigned URL valid for 1 hour, and the detected MIME type.

`backend/shared/storage/presigner.py` — `generate_presigned_url(object_key: str, expiry_seconds: int = 3600) -> str`. Generates a presigned GET URL for an existing object. Used when the frontend needs to display uploaded evidence.

`backend/evidence/` — new feature folder. Add `__init__.py`.

`backend/evidence/service.py` — `upload_evidence(db, file: UploadFile, session_id: UUID, checkpoint_id: str, user_id: UUID, evidence_type: str) -> EvidenceRecord`. FastAPI's `UploadFile` object is the input. Reads all bytes with `await file.read()`. Calls `upload_evidence_file()`. Computes SHA-256 checksum of the bytes: `hashlib.sha256(file_bytes).hexdigest()`. Creates the evidence DB record via repository. Writes audit log `evidence.uploaded`. Returns the record.

`backend/evidence/schemas.py` — `EvidenceUploadResponse` with `evidence_id: UUID`, `checkpoint_id: str`, `artifact_url: str`, `mime_type: str`, `file_size_bytes: int`, `validated: bool`. `EvidenceListResponse` for fetching all evidence for a session.

`backend/evidence/router.py` — two routes: `POST /evidence/upload` — uses `File(...)` and `Form(...)` FastAPI dependencies for multipart. Fields: `file: UploadFile = File(...)`, `session_id: UUID = Form(...)`, `checkpoint_id: str = Form(...)`, `evidence_type: str = Form(...)`. Returns `EvidenceUploadResponse`. `GET /evidence/session/:session_id` — returns all evidence records for a session.

`backend/shared/db/repositories/evidence_repository.py` — `create(session, data) -> EvidenceModel`, `get_by_session(session, session_id) -> list[EvidenceModel]`, `get_by_checkpoint(session, session_id, checkpoint_id) -> list[EvidenceModel]`, `mark_validated(session, evidence_id, result: dict)`, `get_unvalidated(session) -> list[EvidenceModel]`.

Add migration `016_create_evidence.py`.

**Local development without S3**

Add `minio` service to `docker-compose.yml`. MinIO is an S3-compatible local object storage server. Set `S3_ENDPOINT_URL=http://localhost:9000` in `.env.local`. Set `S3_ACCESS_KEY_ID=minioadmin`, `S3_SECRET_ACCESS_KEY=minioadmin`. Add a `make create-bucket` Makefile target that runs `aws s3 mb s3://skillos-dev --endpoint-url http://localhost:9000`. This gives you full S3 API compatibility locally without touching real AWS.

`docker-compose.yml` additions:
```yaml
minio:
  image: minio/minio:latest
  command: server /data --console-address ":9001"
  ports:
    - "9000:9000"
    - "9001:9001"
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin
  volumes:
    - minio_data:/data
```

**Tests**

`tests/evidence/test_uploader.py` — mock `aioboto3` client using `AsyncMock`. Test valid PNG upload succeeds and returns correct MIME type. Test that a `.txt` file with a renamed `.jpg` extension is detected as `text/plain` by `python-magic` and passes if text/plain is in the allowed set. Test that a file with MIME type `application/x-executable` raises `BusinessError("unsupported_mime_type")`. Test file over 50MB raises `BusinessError("file_too_large")`. Test that the object key contains the session_id and checkpoint_id.

`tests/evidence/test_service.py` — integration test using MinIO if available in test environment, otherwise mock. Upload a real PNG file bytes, assert evidence record created in DB with correct fields, assert `validated=False` initially.

---

## Step 16 — Validation engine

**What it is**

Evaluates evidence against checkpoint thresholds and produces a binary pass or fail. No partial credit. No subjective judgment. Three evidence types each have a different validation method. The validation engine is called after the session completes and evidence is uploaded.

**No new packages**

All needed libraries are installed. The LLM gateway from step 10 is used for artifact validation.

**Files to create**

`backend/validation/` — new feature folder. Add `__init__.py`.

`backend/validation/validators.py` — three pure validation functions, one per evidence type.

`validate_numeric(evidence_payload: dict, threshold: float) -> ValidationResult`:
Extracts numeric values from the payload. The primary metric is the one that corresponds to the checkpoint type — for accuracy-based checkpoints it is `accuracy_pct`, for time-based it is `time_taken_seconds`, for error-count-based it is `error_count`. The checkpoint `pass_criteria` string is parsed to determine which metric and what direction (above threshold or below threshold). Returns `ValidationResult(passed=value >= threshold, threshold=threshold, actual=value, reason="metric comparison")`.

```python
@dataclass
class ValidationResult:
    passed: bool
    threshold: float
    actual: float | str
    reason: str
    evidence_type: str
```

`validate_behavioral_log(evidence_payload: dict, required_steps: list[str]) -> ValidationResult`:
Checks that all required step IDs appear in `evidence_payload["steps_completed"]`. Also checks `evidence_payload["retry_count"] <= max_retries` derived from `LearningParameters.retry_limit`. Returns pass if both conditions met, fail with reason if either fails.

`validate_artifact(evidence_payload: dict, artifact_url: str, checkpoint_description: str, pass_criteria: str) -> ValidationResult` — this one uses the LLM gateway. Builds a prompt: "You are evaluating evidence for a learning checkpoint. Checkpoint: {checkpoint_description}. Pass criteria: {pass_criteria}. The learner has submitted an artifact. Evaluate whether the artifact meets the pass criteria." However — for a college project, actual image analysis requires vision model capability. Use `claude-sonnet-4-20250514` which has vision. The artifact URL is passed as a presigned URL in the prompt context. The LLM is asked to respond with structured JSON: `{ "passed": bool, "confidence": float, "reason": str }`. Schema validated via gateway. If LLM validation fails both attempts, default to `passed=False, reason="validation_unavailable"` — safe failure. Never default to `passed=True` on LLM failure.

`backend/validation/engine.py` — the orchestration layer for validation:

```python
async def validate_checkpoint(
    db: AsyncSession,
    session_id: UUID,
    checkpoint_id: str,
    params: LearningParameters
) -> ValidationResult:
```

Fetches all evidence records for this session and checkpoint via repository. If no evidence exists → `ValidationResult(passed=False, reason="no_evidence_submitted")`. Groups evidence by type. For each evidence record, calls the appropriate validator. If any evidence record fails → overall result is `failed`. All evidence must pass for the checkpoint to pass — there is no "majority passes" logic. Updates each evidence record with its individual `ValidationResult` via repository. Returns the overall result.

`backend/validation/service.py` — `run_checkpoint_validation(db, session_id, checkpoint_id) -> ValidationResult`. Fetches session, fetches roadmap to get checkpoint definition (threshold, evidence type, pass criteria), fetches learning parameters, calls `validate_checkpoint()`. Calls orchestration layer to transition checkpoint state (step 17). Writes audit log `checkpoint.passed` or `checkpoint.failed`. If passed, checks if all checkpoints in the phase are now passed — if yes, calls orchestration layer to advance the roadmap phase.

`backend/validation/router.py` — `POST /checkpoint/validate` with body `{ session_id: UUID, checkpoint_id: str }`. Returns `ValidationResult` serialized. Requires auth.

`backend/shared/db/repositories/checkpoint_repository.py` — stores checkpoint state per roadmap. This requires a `checkpoint_states` table.

Add migration `017_create_checkpoint_states.py` with columns: `id UUID`, `roadmap_id UUID FK`, `phase_slug VARCHAR(64)`, `checkpoint_id VARCHAR(64)`, `status VARCHAR(32)` (pending/attempted/passed/failed), `attempts INT DEFAULT 0`, `last_result JSONB`, `updated_at TIMESTAMPTZ`.

Repository functions: `get_checkpoint_state(session, roadmap_id, checkpoint_id) -> CheckpointStateModel`, `update_checkpoint_state(session, roadmap_id, checkpoint_id, status, result)`, `get_all_phase_checkpoints(session, roadmap_id, phase_slug) -> list[CheckpointStateModel]`, `all_phase_checkpoints_passed(session, roadmap_id, phase_slug) -> bool`.

**Tests**

`tests/validation/test_validators.py`

Numeric tests: `accuracy_pct=0.91`, `threshold=0.85` → `passed=True`. `accuracy_pct=0.70`, `threshold=0.85` → `passed=False`. Test with `error_count` — lower is better, so invert: `error_count=2`, threshold means max 3 errors → `passed=True`.

Behavioral log tests: all required steps present → `passed=True`. One step missing → `passed=False`. Retry count exceeds limit → `passed=False`.

Artifact tests: mock `llm_call` to return `{ "passed": true, "confidence": 0.9, "reason": "..." }` → `passed=True`. Mock to return invalid JSON both times → `passed=False` with `reason="validation_unavailable"`. Never returns `passed=True` on LLM failure — assert this explicitly.

No evidence test: call `validate_checkpoint()` with no evidence records → `passed=False, reason="no_evidence_submitted"`.

All-must-pass test: two numeric evidence records for same checkpoint, one passes and one fails → overall `passed=False`.

---

## Step 17 — Orchestration layer

**What it is**

The single authority over all state transitions in the system. No other module, service, or route handler changes the status of a session, checkpoint, or roadmap phase directly. They all call the orchestration layer. This is enforced by code structure — the repository `update_status` functions are not imported anywhere except the orchestration layer and the orchestration layer itself.

**No new packages**

Pure Python. No new dependencies.

**Files to create**

`backend/orchestration/` — new feature folder. Add `__init__.py`.

`backend/orchestration/state_machine.py` — defines allowed transitions as explicit dicts:

```python
SESSION_TRANSITIONS = {
    "pending":   ["active"],
    "active":    ["completed", "failed"],
    "completed": [],   # terminal
    "failed":    [],   # terminal
}

CHECKPOINT_TRANSITIONS = {
    "pending":   ["attempted"],
    "attempted": ["passed", "failed"],
    "passed":    [],   # terminal
    "failed":    ["attempted"],  # can be re-attempted up to retry_limit
}

ROADMAP_PHASE_TRANSITIONS = {
    "locked":    ["active"],
    "active":    ["completed"],
    "completed": [],   # terminal
}
```

`validate_transition(current: str, target: str, transitions: dict) -> bool` — returns True if the transition is allowed. Raises `BusinessError("invalid_state_transition", current=current, target=target)` if not.

`backend/orchestration/orchestrator.py` — all state transition functions live here and only here:

`transition_session(db, session_id, target_status, failure_reason=None)` — validates transition, calls `session_repository.update_status()`, writes audit log.

`transition_checkpoint(db, roadmap_id, checkpoint_id, target_status, result=None)` — validates transition, calls `checkpoint_repository.update_checkpoint_state()`, increments `attempts` counter, writes audit log.

`transition_roadmap_phase(db, roadmap_id, phase_slug, target_status)` — validates transition, calls `roadmap_repository.update_phase_status()`, writes audit log. If `target_status == "completed"`, also calls `unlock_next_phase()`.

`unlock_next_phase(db, roadmap_id, completed_phase_slug)` — fetches the roadmap structure, determines which phase comes after `completed_phase_slug` based on the order they appear in the `phases` dict, calls `transition_roadmap_phase()` for the next phase with `target_status="active"`. If there is no next phase, marks the roadmap itself as `status="completed"`.

`check_phase_completion(db, roadmap_id, phase_slug) -> bool` — calls `checkpoint_repository.all_phase_checkpoints_passed()`. If True, calls `transition_roadmap_phase(db, roadmap_id, phase_slug, "completed")`. Returns the bool.

**Enforcement at import level**

In `backend/shared/db/repositories/session_repository.py`, `checkpoint_repository.py`, and `roadmap_repository.py` — the `update_status` and state-changing functions have a module-level comment and docstring: "This function is called only by backend/orchestration/orchestrator.py. Do not import or call this function from any other module." This is a convention, not a hard technical enforcement. The hard enforcement is `import-linter` — add a contract in `setup.cfg`:

```ini
[importlinter:contract:orchestration-only]
name = Only orchestration layer may call state-changing repository functions
type = forbidden
source_modules = backend.session.service
                 backend.validation.service
                 backend.roadmap.service
forbidden_modules = backend.shared.db.repositories.session_repository.update_status
```

This is the best Python can do without runtime enforcement. Document it clearly.

**Tests**

`tests/orchestration/test_state_machine.py`

Valid transition tests: `pending → active` for session is valid. `active → completed` is valid. `active → pending` is invalid and raises `BusinessError`. `completed → failed` is invalid and raises.

Checkpoint retry test: `failed → attempted` is valid (allows retry). `passed → attempted` is invalid (cannot re-attempt a passed checkpoint).

Phase unlock test: complete all checkpoints in phase 1, assert phase 2 transitions to `active`. Complete all checkpoints in the last phase, assert roadmap `status` transitions to `completed`.

Roadmap completion test: roadmap with two phases, both completed → roadmap `status="completed"`.

`tests/orchestration/test_orchestrator.py` — integration tests using test DB. Full state machine walkthrough: create session → start → submit metrics → complete → validate checkpoint → assert phase advances if all checkpoints pass.

---

## Step 18 — Job queue

**What it is**

Decouples the two heavy operations — roadmap generation (LLM calls) and checkpoint validation (LLM artifact evaluation) — from the synchronous HTTP request cycle. Instead of the client waiting 10–30 seconds for an LLM response, the API returns immediately with a `job_id`, and the client polls for completion.

**New packages**

Add to `requirements.in`: `celery[redis]` — the task queue. The `redis` extra bundles the Redis broker backend. `redis` is already in requirements from Phase A rate limiting — Celery reuses the same Redis instance. `flower` — add to `requirements-dev.in` only. Flower is a web UI for monitoring Celery workers. Never in production requirements.

Add to `requirements.in`: `kombu` — Celery's messaging library, pulled in transitively but pin explicitly for stability.

Run `pip-compile --generate-hashes requirements.in` and `pip-compile --generate-hashes requirements-dev.in`.

**New environment variables**

Add to `settings.py`: `CELERY_BROKER_URL: str` — same Redis URL as rate limiting, e.g. `redis://localhost:6379/0`. `CELERY_RESULT_BACKEND: str` — use `db+postgresql://` pointing at your PostgreSQL DB so job results are queryable via the existing DB connection. This avoids needing a separate result storage.

**Docker compose additions**

```yaml
celery_worker:
  build: .
  command: celery -A backend.shared.queue.celery_app worker --loglevel=info --concurrency=4
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
  depends_on:
    - redis
    - db

celery_beat:
  build: .
  command: celery -A backend.shared.queue.celery_app beat --loglevel=info
  depends_on:
    - redis
```

The `celery_beat` service runs the scheduled cleanup job that deletes expired tokens from `revoked_access_tokens`.

**Files to create**

`backend/shared/queue/celery_app.py` — creates the Celery application instance:

```python
from celery import Celery
from backend.shared.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "skillos",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["backend.shared.queue.tasks"]
)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.task_time_limit = 120          # hard kill after 2 minutes
celery_app.conf.task_soft_time_limit = 90      # raises SoftTimeLimitExceeded at 90s
celery_app.conf.worker_max_tasks_per_child = 50  # recycle worker after 50 tasks to prevent memory leaks
```

`backend/shared/queue/tasks.py` — defines the two async tasks:

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def generate_roadmap_task(self, user_id: str, skill_id: str):
    # runs synchronous version of roadmap service
    # uses a new sync DB session (not async — Celery workers are sync)
    try:
        with SyncSessionLocal() as db:
            result = sync_create_roadmap(db, UUID(user_id), skill_id)
            return {"roadmap_id": str(result.id), "status": "completed"}
    except Exception as exc:
        raise self.retry(exc=exc)

@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def validate_checkpoint_task(self, session_id: str, checkpoint_id: str):
    try:
        with SyncSessionLocal() as db:
            result = sync_run_checkpoint_validation(db, UUID(session_id), checkpoint_id)
            return {"passed": result.passed, "reason": result.reason, "status": "completed"}
    except Exception as exc:
        raise self.retry(exc=exc)

@celery_app.task
def cleanup_expired_tokens_task():
    with SyncSessionLocal() as db:
        auth_repository.delete_expired_revocations(db)
```

Note the `SyncSessionLocal` — Celery workers run in a synchronous context. You need a synchronous SQLAlchemy session factory alongside the async one. Add `SyncSessionLocal = sessionmaker(create_engine(settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")))` to `backend/shared/db/base.py`. Add `psycopg2-binary` to `requirements.in` for the sync driver.

Also add sync versions of the service functions: `sync_create_roadmap()` and `sync_run_checkpoint_validation()`. These are identical to their async counterparts but use sync SQLAlchemy sessions. They live in the same service files as the async versions, just without `async/await`.

`backend/shared/queue/jobs_repository.py` — since Celery results are stored in PostgreSQL via the result backend, you do not need a custom jobs table. Instead use Celery's built-in `AsyncResult` to query job status: `celery_app.AsyncResult(job_id).state` returns `PENDING`, `STARTED`, `SUCCESS`, `FAILURE`.

`backend/shared/queue/beat_schedule.py` — Celery Beat schedule:

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "backend.shared.queue.tasks.cleanup_expired_tokens_task",
        "schedule": crontab(hour=2, minute=0),  # runs at 2am daily
    }
}
```

**Route updates**

Update `backend/roadmap/router.py`: `POST /roadmap/generate` now enqueues the task instead of calling the service directly. Returns `202 { job_id: str }`. Add `GET /jobs/:job_id` route in a new `backend/shared/jobs/router.py` that calls `celery_app.AsyncResult(job_id)` and returns `{ status: str, result: dict | None }`.

Update `backend/validation/router.py`: `POST /checkpoint/validate` now enqueues `validate_checkpoint_task`. Returns `202 { job_id: str }`.

**Concurrency limits**

Worker concurrency is set to 4 in the docker-compose command. This prevents more than 4 simultaneous LLM calls from one worker instance. At 4 workers, max 4 concurrent roadmap generations or 4 concurrent checkpoint validations. LLM API rate limits are the bottleneck — 4 concurrent is safe for standard API tier limits.

Dead letter queue: tasks that exhaust all retries (`max_retries`) are logged as `FAILURE` in Celery's result backend. Add a monitoring alert: if `AsyncResult.state == "FAILURE"` and `AsyncResult.date_done > threshold`, send an alert. For Phase C this is just a logged error. Phase D adds monitoring.

**Tests**

`tests/queue/test_tasks.py` — use Celery's `task_always_eager` setting in test configuration: `celery_app.conf.task_always_eager = True`. This makes tasks execute synchronously in tests — no actual worker needed. With `task_always_eager=True`, `generate_roadmap_task.delay(user_id, skill_id)` runs immediately and returns the result.

Test roadmap task: mock `sync_create_roadmap`, call task, assert mock was called with correct arguments, assert return value has `roadmap_id` and `status="completed"`.

Test retry behavior: mock `sync_create_roadmap` to raise an exception on first two calls, succeed on third. Assert task retried correctly and final result is success.

Test checkpoint task: same pattern — mock `sync_run_checkpoint_validation`, verify result structure.

Test cleanup task: mock `auth_repository.delete_expired_revocations`, call task, assert it was called once.

Job status test: after `task_always_eager` task completes, call `AsyncResult(task_id).state` and assert `"SUCCESS"`.

---

## Phase C completion gate

Phase C is complete when all of the following are true:

`tests/roadmap/`, `tests/session/`, `tests/evidence/`, `tests/validation/`, `tests/orchestration/`, `tests/queue/` all pass with zero failures.

Determinism test passes: `generate_roadmap()` called 100 times with the same inputs produces identical `fingerprint` every time.

`verify_roadmap_integrity()` returns `True` for every generated roadmap in the test database.

A full end-to-end smoke test completes: register user → complete assessment → generate roadmap (via job queue) → start session → submit metrics → complete session → upload evidence → validate checkpoint → assert checkpoint state is `passed` → assert phase advances.

Migrations 014 through 017 all have working `downgrade()` functions verified against the test database.

The job queue smoke test: `POST /roadmap/generate` returns `202` with a `job_id`, polling `GET /jobs/:job_id` eventually returns `{ status: "SUCCESS", result: { roadmap_id: "..." } }`.

MinIO is running in docker-compose and evidence upload integration test stores a real file and retrieves it via presigned URL.

No service file outside `backend/orchestration/orchestrator.py` directly calls any `update_status` or state-transition repository function — verified by import-linter in CI.