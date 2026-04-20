Phase B — everything needed, in full detail.

---

## Phase B starts with one rule

Phase A must be complete and all tests passing before a single Phase B file is written. The reason is concrete: steps 9, 11, and 12 all take a `ProfileVector` or `LearningParameters` object as input. If those objects are not stable and tested, everything built on top of them in Phase B will produce wrong outputs silently.

---

## Step 8 — Skill template schema

**What it is**

A skill template is the static knowledge structure that defines what learning a skill looks like. It is not generated — it is authored once and stored. The roadmap generator in Phase C reads it. The LLM in step 11 reads it. It must exist and be stable before either of those can be built.

**Package needed**

No new packages. SQLAlchemy is already installed. JSONB column type is already in SQLAlchemy. You need `jsonschema` added to `requirements.in` — this is used to validate the structure JSONB against a defined schema before insert, so malformed templates cannot enter the database.

`pip-compile` again after adding `jsonschema` to regenerate the locked `requirements.txt`.

**Files to create**

`backend/skill/` — new feature folder. Add `__init__.py`.

`backend/skill/template_schema.py` — defines the expected JSON structure as a Python dict that serves as a JSONSchema validator. This is the single source of truth for what a valid skill template looks like. The schema enforces that `skill_id` is a string, `phases` is an object, each phase has `competencies` as a list of strings, `techniques` as a list of strings, and `checkpoints` as a list of strings. Import `jsonschema.validate` here and expose a `validate_template_structure(data: dict)` function that raises `jsonschema.ValidationError` on invalid input.

```python
SKILL_TEMPLATE_SCHEMA = {
    "type": "object",
    "required": ["phases"],
    "properties": {
        "phases": {
            "type": "object",
            "minProperties": 1,
            "additionalProperties": {
                "type": "object",
                "required": ["competencies", "techniques", "checkpoints"],
                "properties": {
                    "competencies": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "techniques":   {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "checkpoints":  {"type": "array", "items": {"type": "string"}, "minItems": 1}
                }
            }
        }
    }
}
```

`backend/shared/db/models/skill_template.py` — SQLAlchemy ORM model for the `skill_templates` table. Fields: `id UUID`, `skill_id VARCHAR(64)`, `version INT`, `name VARCHAR(128)`, `domain VARCHAR(64)`, `complexity_score NUMERIC(4,3)`, `structure JSONB`, `is_active BOOLEAN`, `created_at TIMESTAMPTZ`. Uses `Mapped[dict]` for the JSONB column with `mapped_column(JSONB)` — import `JSONB` from `sqlalchemy.dialects.postgresql`.

`backend/shared/db/repositories/skill_template_repository.py` — DB queries only. Functions: `get_active_template(session, skill_id) -> SkillTemplate | None` — fetches the latest active version. `get_template_by_version(session, skill_id, version) -> SkillTemplate | None` — used when roadmaps pin to a specific version. `create_template(session, data) -> SkillTemplate` — validates structure via `validate_template_structure()` before insert, raises `BusinessError` if invalid. `list_active_skills(session) -> list[SkillTemplate]` — returns all active skill slugs and names for the UI selection screen.

`backend/skill/service.py` — business logic. `create_skill_template(db, payload) -> SkillTemplate` — calls validator, increments version if skill_id already exists, sets `is_active=True`, deactivates previous version. `get_skill(db, skill_id) -> SkillTemplate` — raises `BusinessError("skill_not_found")` if no active template.

`backend/skill/router.py` — two routes for now. `GET /skills` returns the list of available skills. `POST /skills` is admin-only and creates a new template. Admin protection is a simple check: `if current_user.status != "admin": raise HTTPException(403)`. No full RBAC system needed for a college project.

`backend/skill/schemas.py` — `SkillTemplateCreate` Pydantic model with all fields. `SkillTemplateResponse` for API output. The `structure` field is typed as `dict` in Pydantic.

**Seed data**

Create `scripts/seed_skills.py`. This script reads JSON files from a `data/skill_templates/` folder and inserts them via the repository. Each JSON file is one skill. Start with at minimum two skills — one motor-heavy like `drawing` and one cognitive-heavy like `python-basics`. This gives you enough variety to test parameter-skill mapping in step 12.

Example `data/skill_templates/drawing.json`:
```json
{
  "skill_id": "drawing",
  "name": "Drawing",
  "domain": "art",
  "complexity_score": 0.65,
  "structure": {
    "phases": {
      "fundamentals": {
        "competencies": ["line control", "basic shapes", "proportions"],
        "techniques": ["blind contour", "gesture drawing", "grid method"],
        "checkpoints": ["produce 5 shapes within 5% proportion error", "complete 3 gesture drawings in 60 seconds each"]
      },
      "intermediate": {
        "competencies": ["shading", "perspective", "composition"],
        "techniques": ["hatching", "one-point perspective", "rule of thirds"],
        "checkpoints": ["demonstrate 3 shading techniques on a sphere", "draw a room in one-point perspective"]
      }
    }
  }
}
```

**Tests**

`tests/skill/test_template_schema.py` — test `validate_template_structure()` with a valid template passes, missing `competencies` key raises `ValidationError`, empty `checkpoints` array raises `ValidationError`, wrong type for `techniques` raises `ValidationError`.

`tests/skill/test_skill_service.py` — test that creating a skill with an invalid structure raises `BusinessError`, creating a valid skill returns a `SkillTemplate` object, creating a second version of the same skill deactivates the previous one, `get_skill` on nonexistent skill_id raises `BusinessError`.

---

## Step 9 — Skill grounding probes

**What it is**

Three lightweight probe types administered to the user after they select a skill. Not an assessment of actual ability — it captures what the user believes about their own ability. The output is a `BaselineSkillState` object with a `confidence_bias` field. This value equals perceived level minus actual level derived from the ProfileVector. It feeds into step 11 and can adjust `repetition_intensity` thresholds.

**No new packages needed**

Everything is in Pydantic and SQLAlchemy already installed.

**Files to create**

`backend/skill/grounding.py` — the core computation file. Defines three probe types as string literals: `"recognition"`, `"familiarity"`, `"confidence_estimation"`. Defines `BaselineSkillState` as a typed dataclass:

```python
@dataclass
class BaselineSkillState:
    skill_id: str
    user_id: UUID
    exposure_score: float        # 0-1 from recognition task
    declarative_score: float     # 0-1 from familiarity MCQ
    confidence_score: float      # 0-1 from self-rating
    perceived_level: float       # average of the three
    actual_level: float          # derived from ProfileVector cognitive_capacity
    confidence_bias: float       # perceived_level - actual_level, range [-1, 1]
    created_at: datetime
```

`compute_baseline(probe_responses: GroundingProbeResponses, profile: ProfileVector, skill_id: str) -> BaselineSkillState` — the pure computation function. `exposure_score` is the proportion of recognition items the user marked as familiar (0–1). `declarative_score` is the proportion of MCQ answers that were correct (0–1). `confidence_score` is the self-rating normalized to 0–1 (user rates 1–5, divide by 5). `perceived_level` is the unweighted average of the three. `actual_level` is `profile.cognitive_capacity` as the closest proxy from the ProfileVector. `confidence_bias` is `perceived_level - actual_level`, clamped to `[-1, 1]`. Positive value means overconfident. Negative means underconfident.

`backend/skill/grounding_schemas.py` — Pydantic models. `RecognitionProbeResponse` — list of booleans, one per item shown. `FamiliarityProbeResponse` — list of selected answer indices. `ConfidenceProbeResponse` — integer 1–5. `GroundingProbeResponses` — wraps all three. `BaselineSkillStateResponse` — the API output model.

`backend/shared/db/models/baseline_skill_state.py` — ORM model for persisting the `BaselineSkillState`. Table name: `baseline_skill_states`. Columns: `id UUID`, `user_id UUID FK users.id`, `skill_id VARCHAR(64)`, `profile_version INT`, `exposure_score NUMERIC(5,4)`, `declarative_score NUMERIC(5,4)`, `confidence_score NUMERIC(5,4)`, `perceived_level NUMERIC(5,4)`, `actual_level NUMERIC(5,4)`, `confidence_bias NUMERIC(6,5)`, `raw_responses JSONB`, `created_at TIMESTAMPTZ`.

`backend/shared/db/repositories/grounding_repository.py` — `create_baseline(session, state: BaselineSkillState, raw_responses: dict) -> BaselineSkillStateModel`, `get_latest_baseline(session, user_id, skill_id) -> BaselineSkillStateModel | None`.

`backend/skill/grounding_service.py` — `submit_grounding(db, user_id, skill_id, responses, profile) -> BaselineSkillState`. Fetches the active profile, fetches active skill template (validates skill exists), calls `compute_baseline()`, persists via repository, writes audit log entry `skill.grounding_completed`, returns the `BaselineSkillState`.

Add migration `012_create_baseline_skill_states.py` to Alembic.

Route added to `backend/skill/router.py`: `POST /skill/baseline` — requires auth, calls grounding service, returns `BaselineSkillStateResponse`.

**Probe content**

The actual probe questions are stored in the skill template. Add a `grounding_probes` key to the skill template structure:

```json
"grounding_probes": {
  "recognition": ["blind contour drawing", "gesture drawing", "hatching", "one-point perspective"],
  "familiarity": [
    {
      "question": "What does 'value' mean in drawing?",
      "options": ["Color temperature", "Lightness or darkness", "Line weight", "Texture"],
      "correct_index": 1
    }
  ]
}
```

The confidence probe is always the same format — "Rate your ability from 1 (never tried) to 5 (can teach others)" — so it does not need to be stored in the template.

Update `SKILL_TEMPLATE_SCHEMA` in `template_schema.py` to include `grounding_probes` as an optional key. Update seed JSON files to include it.

**Tests**

`tests/skill/test_grounding.py` — test `compute_baseline()` with a known probe response set and known ProfileVector, assert `confidence_bias` equals expected value to 4 decimal places. Test that a perfectly calibrated user (perceived == actual) produces `confidence_bias == 0.0`. Test that an overconfident user (high self-rating, low ProfileVector) produces positive `confidence_bias`. Test that an underconfident user produces negative `confidence_bias`. Test clamping: responses that would produce `confidence_bias > 1.0` are clamped to 1.0.

---

## Step 10 — LLM gateway

**What it is**

A thin wrapper around the Anthropic or OpenAI API that enforces three constraints on every call: temperature is always 0 for structured output calls, the response is always validated against a Pydantic schema, and failure triggers exactly one retry before falling back to conservative defaults. Nothing upstream of this wrapper calls the LLM API directly. Everything goes through this gateway.

**New packages**

Add to `requirements.in`: `anthropic` — the official Anthropic Python SDK. This is preferable to OpenAI for this project because the SDK is cleaner for structured output patterns and the `claude-sonnet-4-20250514` model is specified in your technical plan. Also add `tenacity` — for retry logic with exponential backoff. Do not implement retry logic manually.

Run `pip-compile --generate-hashes requirements.in` again.

**New environment variables**

Add to `settings.py`: `ANTHROPIC_API_KEY: str`, `LLM_MODEL: str = "claude-sonnet-4-20250514"`, `LLM_MAX_TOKENS: int = 1000`, `LLM_TEMPERATURE: float = 0.0`. These are read from secrets manager in production, from `.env.local` in development.

**Files to create**

`backend/shared/llm/gateway.py` — the core file. Everything in Phase B that calls the LLM goes through functions defined here.

The gateway defines a single primary function:

```python
async def llm_call(
    prompt: str,
    system_prompt: str,
    response_schema: type[BaseModel],
    fallback: BaseModel,
    temperature: float = 0.0
) -> BaseModel:
```

Internally it does: builds the Anthropic message with `system` and `user` roles. Calls `anthropic.messages.create()` with `model`, `max_tokens`, `temperature`, and the messages list. Extracts the text content from the response. Attempts `response_schema.model_validate_json(content)`. If Pydantic validation fails, retries once — same call, same parameters. If second attempt also fails validation, logs a WARNING with the raw response content and returns `fallback`. If the API call itself raises an exception (network error, rate limit, API error), uses `tenacity` with `@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))` decorator. If both attempts fail at the API level, raises `SystemError("llm_gateway_failure")` which the global exception handler converts to a 503.

`backend/shared/llm/prompts.py` — all prompt templates as module-level string constants. No f-string prompt building in service files — all prompt construction happens here. This makes prompts auditable and testable. Functions like `build_feasibility_prompt(profile: ProfileVector, skill: SkillTemplate) -> str` that take typed inputs and return complete prompt strings. This file will grow as Phase B progresses.

`backend/shared/llm/schemas.py` — all Pydantic schemas for LLM response validation. These are the schemas that the gateway validates against. One schema per LLM call type. Defined here and imported by both the gateway and the skill intelligence engine.

`backend/shared/llm/client.py` — a singleton Anthropic client. Creates `anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)` once using `@lru_cache`. The gateway imports this. Keeps connection pooling efficient.

**LLM response schemas to define in `llm/schemas.py`**

For the four LLM calls in step 11:

```python
class FeasibilityResult(BaseModel):
    feasible: bool
    risk_level: Literal["low", "medium", "high"]
    blockers: list[str]
    confidence: float  # 0-1

class RiskZoneResult(BaseModel):
    risks: list[RiskItem]

class RiskItem(BaseModel):
    dimension: str
    type: str
    severity: Literal["low", "medium", "high"]

class TimeModelResult(BaseModel):
    estimated_weeks: int
    hours_per_phase: dict[str, float]
    confidence: float

class SkillModifierResult(BaseModel):
    technique_density_adjustment: float  # -0.3 to 0.3
    repetition_boost: float              # -0.3 to 0.3
    notes: str
```

**Conservative fallbacks**

For each schema, define a fallback instance that represents the safest possible assumption. For feasibility: `feasible=True, risk_level="medium", blockers=[]`. For risk zones: `risks=[]`. For time model: `estimated_weeks=12, hours_per_phase={}`. For skill modifiers: `technique_density_adjustment=0.0, repetition_boost=0.0`. These are used when both LLM attempts fail validation. The system continues rather than crashing — it just uses generic defaults.

**Tests**

`tests/llm/test_gateway.py` — mock the Anthropic client using `unittest.mock.AsyncMock`. Test that valid JSON response returns validated Pydantic model. Test that invalid JSON response triggers one retry. Test that two consecutive invalid responses returns the fallback. Test that API exception triggers retry then raises `SystemError`. Test that `temperature` is always passed as 0.0 in the API call arguments regardless of what caller passes. That last test is important — it verifies the constraint is enforced at the gateway level, not trusted from callers.

---

## Step 11 — Skill intelligence engine

**What it is**

Takes the `ProfileVector`, `BaselineSkillState`, and `SkillTemplate` and makes four sequential LLM calls to produce a `SkillResearchObject`. This object is the complete intelligence package that the roadmap generator in Phase C will consume. It must be produced before any roadmap can exist.

**No new packages**

Everything needed is already installed from step 10.

**Files to create**

`backend/skill/intelligence.py` — the main engine file. Defines `SkillResearchObject` as a Pydantic model:

```python
class SkillResearchObject(BaseModel):
    skill_id: str
    user_id: UUID
    profile_version: int
    feasibility: FeasibilityResult
    risk_zones: RiskZoneResult
    time_model: TimeModelResult
    skill_modifiers: SkillModifierResult
    confidence_bias: float
    generated_at: datetime
    
    # Derived convenience fields
    is_feasible: bool
    estimated_weeks: int
    overall_risk: Literal["low", "medium", "high"]
```

`compute_skill_research(profile: ProfileVector, baseline: BaselineSkillState, template: SkillTemplate) -> SkillResearchObject` — the orchestration function. Makes four `llm_call()` invocations in sequence. Each uses a prompt built by a function in `llm/prompts.py`. All four calls use `temperature=0.0`. Returns the assembled `SkillResearchObject`.

The four calls in order:

**Call 1 — Feasibility analysis.** Prompt includes `cognitive_capacity`, `time_constraint`, `skill complexity_score`, `confidence_bias`. System prompt instructs the model to evaluate whether the learner's profile supports acquiring this skill within a reasonable timeframe. Response schema: `FeasibilityResult`. Fallback: conservative medium-risk feasible result.

**Call 2 — Risk zone detection.** Prompt includes the full ProfileVector all 6 dimensions with their values, and the skill domain. System prompt instructs the model to identify which ProfileVector dimensions represent potential failure points for this specific skill. Response schema: `RiskZoneResult`. Fallback: empty risks list.

**Call 3 — Time modelling.** Prompt includes learning parameters (specifically `phase_pacing`, `session_duration`, `difficulty_slope`), skill template phase list, and `time_constraint`. System prompt instructs the model to estimate realistic week counts per phase. Response schema: `TimeModelResult`. Fallback: 12 weeks total with equal distribution across phases.

**Call 4 — Skill modifier derivation.** Prompt includes skill domain, `motor_baseline`, `cognitive_capacity`, and the skill's `complexity_score`. System prompt instructs the model to derive adjustment values for `technique_density` and `repetition_intensity` specific to this skill type. Response schema: `SkillModifierResult`. Fallback: zero adjustments.

After all four calls, the function populates the derived convenience fields: `is_feasible` from `feasibility.feasible`, `estimated_weeks` from `time_model.estimated_weeks`, `overall_risk` from `feasibility.risk_level`.

**Prompt construction in `llm/prompts.py`**

Add four functions: `build_feasibility_prompt()`, `build_risk_zone_prompt()`, `build_time_model_prompt()`, `build_skill_modifier_prompt()`. Each takes typed inputs, not raw dicts. Each returns a complete prompt string. The system prompt for all four contains: "You are the SkillOS intelligence engine. Respond ONLY with valid JSON matching the provided schema. No explanation, no markdown, no preamble."

**Persistence**

`backend/shared/db/models/skill_research.py` — ORM model for `skill_research_objects` table. Columns: `id UUID`, `user_id UUID FK`, `skill_id VARCHAR(64)`, `profile_version INT`, `payload JSONB` (the full `SkillResearchObject` serialized), `created_at TIMESTAMPTZ`. The full object is stored as JSONB — no column-per-field because this object is consumed whole by the roadmap generator.

Add migration `013_create_skill_research_objects.py`.

`backend/shared/db/repositories/skill_research_repository.py` — `create(session, obj: SkillResearchObject) -> SkillResearchObjectModel`, `get_latest(session, user_id, skill_id) -> SkillResearchObjectModel | None`.

`backend/skill/intelligence_service.py` — `generate_skill_research(db, user_id, skill_id) -> SkillResearchObject`. Fetches active profile, fetches latest baseline state (raises `BusinessError("grounding_required")` if none exists — grounding must happen before intelligence), fetches active skill template, calls `compute_skill_research()`, persists result, writes audit log `skill.research_generated`, returns the object.

Route added to `backend/skill/router.py`: `POST /skill/research` — requires auth, calls intelligence service, returns serialized `SkillResearchObject`. This is an async job candidate — LLM calls take seconds. For Phase B, it runs synchronously. Phase C adds the job queue around it.

**Tests**

`tests/skill/test_intelligence.py` — mock `llm_call` at the module level using `unittest.mock.patch`. Test that all four calls are made with `temperature=0.0`. Test that `SkillResearchObject` is correctly assembled from the four mocked results. Test that if one LLM call returns a fallback, the overall object is still assembled (does not raise). Test `is_feasible` and `overall_risk` derived fields are computed correctly from the sub-results. Test that calling `generate_skill_research` without a prior baseline raises `BusinessError`.

---

## Step 12 — Parameter–skill mapping layer

**What it is**

Takes the general `LearningParameters` computed from the ProfileVector and applies skill-specific adjustments. The same cognitive profile produces different learning parameters for drawing vs programming vs music. This layer is where that differentiation happens. It runs after the `SkillResearchObject` is available because the skill modifiers from call 4 in step 11 are inputs here.

**No new packages**

Pure Python computation. No new dependencies.

**Files to create**

`backend/assessment/skill_mapping.py` — the entire step lives in this one file. Pure functions, no DB calls, no imports except from your own profiling module.

Define an enum or string literals for skill domains: `"art"`, `"music"`, `"programming"`, `"language"`, `"physical"`, `"other"`.

Define override rules as a dict of domain to adjustment function. Each adjustment function takes a `LearningParameters` object and returns a modified copy — it never mutates the original. Example:

```python
DOMAIN_OVERRIDES: dict[str, Callable[[LearningParameters], LearningParameters]] = {
    "art":         _apply_art_overrides,
    "music":       _apply_music_overrides,
    "programming": _apply_programming_overrides,
    "language":    _apply_language_overrides,
}
```

`_apply_art_overrides(params: LearningParameters) -> LearningParameters`:
- Increase `difficulty_slope` weight toward `motor_baseline` by adding 0.15 to it, then clamp
- Increase `drill_depth` by 0.1 (art requires more repetitive physical practice)
- Tighten `checkpoint_rigidity` — multiply by 1.1, clamp to 1.0

`_apply_music_overrides(params: LearningParameters) -> LearningParameters`:
- Increase `repetition_intensity` by 0.15 (music requires high repetition for motor memory)
- Set `repetition_intensity` minimum to 0.6 regardless of ProfileVector — enforced floor
- Tighten `checkpoint_rigidity` on motor checkpoints — multiply by 1.2, clamp

`_apply_programming_overrides(params: LearningParameters) -> LearningParameters`:
- Increase `abstraction_level` by 0.1 (programming is heavily abstract)
- Reduce `technique_density` during fundamentals phase — cap at 0.5 if `cognitive_capacity < 0.6`
- Increase `instruction_granularity` by 0.1 for lower-capacity learners

`_apply_language_overrides(params: LearningParameters) -> LearningParameters`:
- Increase `phase_pacing` for vocabulary phases by 0.1
- Reduce `phase_pacing` for grammar phases by 0.1
- Increase `variation_intensity` by 0.1 (language benefits from varied exposure contexts)

Global override rules applied after domain overrides regardless of domain:
- If `technique_density > 0.7` and skill `complexity_score > 0.7`: cap `technique_density` at 0.7
- If original `learning_tolerance < 0.4`: enforce `repetition_intensity >= 0.6`

**Modifier integration from SkillResearchObject**

After domain overrides and global rules, apply the LLM-derived modifiers from the `SkillResearchObject`:
- `technique_density += skill_modifiers.technique_density_adjustment`, then clamp
- `repetition_intensity += skill_modifiers.repetition_boost`, then clamp
- But the global minimum rules apply after this too — modifiers cannot bypass them

**Main function**

```python
def apply_skill_mapping(
    params: LearningParameters,
    domain: str,
    complexity_score: float,
    skill_modifiers: SkillModifierResult
) -> LearningParameters:
```

Returns a new `LearningParameters` instance with all adjustments applied. The original is never mutated. The returned object has a flag or annotation indicating it is a skill-adjusted copy — not the raw ProfileVector-derived parameters. This matters for auditability.

**LearningParameters dataclass update**

Go back to `backend/assessment/parameters.py` and add two fields to the `LearningParameters` dataclass: `is_skill_adjusted: bool = False` and `skill_id: str | None = None`. The raw derivation sets both to their defaults. The skill mapping function sets `is_skill_adjusted=True` and `skill_id` to the skill being mapped.

**Persistence**

The skill-adjusted parameters are stored in the `learning_parameters` table with the `skill_id` column already defined in the schema. The raw parameters (no skill override) are stored with `skill_id = "baseline"`. The adjusted parameters are stored with the actual skill_id. The roadmap generator always uses the skill-specific row.

Route added to `backend/skill/router.py` is not needed yet — skill mapping is called internally by the intelligence service after step 11 completes. It does not have its own endpoint. The full flow is: generate skill research → apply skill mapping → store adjusted parameters → return to caller.

Update `backend/skill/intelligence_service.py` to call `apply_skill_mapping()` after `compute_skill_research()` returns and before persisting. The service now also calls the parameter derivation repository to store the adjusted `LearningParameters` row with the `skill_id` set.

**Tests**

`tests/skill/test_skill_mapping.py` — test each domain override function in isolation. For art: verify `drill_depth` increased, verify `checkpoint_rigidity` is higher than input. For music: verify `repetition_intensity >= 0.6` regardless of input value, test with input `repetition_intensity=0.2` and assert output is `0.6`. For programming: test with `cognitive_capacity=0.5` and verify `technique_density` is capped at 0.5. Global override test: create params with `technique_density=0.9` and `complexity_score=0.8`, verify output `technique_density == 0.7`. Low tolerance floor test: create params with `learning_tolerance=0.3`, verify `repetition_intensity >= 0.6` in output. Modifier integration test: verify LLM modifier values are added and clamped correctly. Immutability test: verify the input `LearningParameters` object is unchanged after the function returns.

---

## Phase B completion gate

Phase B is complete when all of the following pass:

Every test in `tests/skill/` passes. Every test in `tests/llm/` passes. The LLM gateway tests pass with mocked API — not against the real API. Real API calls are only made in manual integration smoke tests, not in CI. The seed script `scripts/seed_skills.py` runs successfully and two skill templates exist in the database. Calling `POST /skill/baseline` with a valid JWT and valid probe responses returns a `BaselineSkillStateResponse` with all fields populated. Calling `POST /skill/research` triggers four mocked LLM calls and returns a `SkillResearchObject`. The adjusted `LearningParameters` row for the skill exists in the database after research generation. Migration 012 and 013 both have working `downgrade()` functions tested against the test database.