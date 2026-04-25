I'll read all project files systematically before producing the technical map.All documents are already in context. I'll now produce the full technical map.

---

# SkillOS — Full Technical Project Map

---

## Completion Status — ACTUAL vs. SPEC (version_2 branch)

### ✅ Completed
1. ✅ Project directory structure — backend modular layout exists
2. ✅ Backend main registration (main.py) — FastAPI app created with routers
3. ✅ Core API routes — auth, assessment, profile, skill, roadmap, session routers exist
4. ✅ Frontend routing structure — React Router v6 with ProtectedRoute
5. ✅ Auth middleware and services — implemented
6. ✅ Environment variables and config — backend/shared/config.py exists
7. ✅ Rate limiting and error handling — SlowAPI middleware in place
8. ✅ Frontend stores — assessmentStore, profileStore, roadmapStore, sessionStore created
9. ✅ Frontend API client layer — all 10 API files created (auth, assessment, profile, skill, roadmap, session, evidence, checkpoint, resource, doubt, tip, axios)
10. ✅ Layout components — AppShell, Sidebar, TopBar created
11. ✅ Backend service layer — parameter_service, validation_service, llm_service, rag_service created
12. ✅ Frontend views — ProfileView, SkillSelectView, GroundingView, CheckpointView, ResourcesView, DoubtView created (all 11 pages now exist)

### ⚠️ Partial (Skeleton/Foundation Implemented)
13. ⚠️ Data schema (models) — basic models exist; need full SQLAlchemy/Pydantic migration
14. ⚠️ CRUD operations — basic layer exists; needs full implementation with DB operations
15. ⚠️ Frontend components — view structure exists; needs UI polish with shadcn/ui components
16. ⚠️ RAG service — skeleton with mock retrieval; needs pgvector integration
17. ⚠️ LLM service — basic interface created; needs actual API key wiring

### ❌ Not Yet Started
18. ❌ Evidence upload/validation system — backend file handling
19. ❌ Async roadmap generation job queue — Celery integration
20. ❌ Assessment battery UI polish — 6-level assessment display
21. ❌ Tip generation system (failure-triggered)

---

## SECTION 1 — PROJECT DIRECTORY STRUCTURE

```
skillos/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   │   ├── axiosClient.ts
│   │   │   ├── authApi.ts
│   │   │   ├── assessmentApi.ts
│   │   │   ├── profileApi.ts
│   │   │   ├── skillApi.ts
│   │   │   ├── roadmapApi.ts
│   │   │   ├── sessionApi.ts
│   │   │   ├── evidenceApi.ts
│   │   │   ├── checkpointApi.ts
│   │   │   ├── resourceApi.ts
│   │   │   ├── doubtApi.ts
│   │   │   └── tipApi.ts
│   │   ├── components/
│   │   │   ├── ui/               ← shadcn auto-generated components
│   │   │   ├── layout/
│   │   │   │   ├── AppShell.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── TopBar.tsx
│   │   │   │   └── ProtectedRoute.tsx
│   │   │   ├── assessment/
│   │   │   │   ├── AssessmentCard.tsx
│   │   │   │   ├── LivesIndicator.tsx
│   │   │   │   ├── QuestionBlock.tsx
│   │   │   │   ├── TimerBar.tsx
│   │   │   │   └── LevelBadge.tsx
│   │   │   ├── profile/
│   │   │   │   ├── ProfileRadarChart.tsx
│   │   │   │   ├── DimensionBar.tsx
│   │   │   │   └── ProfileSummaryCard.tsx
│   │   │   ├── roadmap/
│   │   │   │   ├── RoadmapTimeline.tsx
│   │   │   │   ├── PhaseCard.tsx
│   │   │   │   ├── CheckpointItem.tsx
│   │   │   │   └── TechniqueTag.tsx
│   │   │   ├── session/
│   │   │   │   ├── SessionProtocolStepper.tsx
│   │   │   │   ├── MetricsCapturePanel.tsx
│   │   │   │   ├── EvidenceUploader.tsx
│   │   │   │   └── SessionStatusBadge.tsx
│   │   │   ├── skill/
│   │   │   │   ├── SkillSelectorCard.tsx
│   │   │   │   ├── GroundingProbeForm.tsx
│   │   │   │   └── BaselineStateDisplay.tsx
│   │   │   ├── support/
│   │   │   │   ├── DoubtPanel.tsx
│   │   │   │   ├── TipCard.tsx
│   │   │   │   └── ResourceList.tsx
│   │   │   └── shared/
│   │   │       ├── LoadingSpinner.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       ├── PageHeader.tsx
│   │   │       └── StatusPill.tsx
│   │   ├── pages/
│   │   │   ├── AuthPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── AssessmentPage.tsx
│   │   │   ├── ProfilePage.tsx
│   │   │   ├── SkillSelectPage.tsx
│   │   │   ├── GroundingPage.tsx
│   │   │   ├── RoadmapPage.tsx
│   │   │   ├── SessionPage.tsx
│   │   │   ├── CheckpointPage.tsx
│   │   │   ├── ResourcesPage.tsx
│   │   │   └── DoubtPage.tsx
│   │   ├── store/
│   │   │   ├── authStore.ts
│   │   │   ├── assessmentStore.ts
│   │   │   ├── profileStore.ts
│   │   │   ├── roadmapStore.ts
│   │   │   └── sessionStore.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── lib/
│   │   │   └── utils.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── cognitive_profile.py
│   │   │   ├── learning_parameters.py
│   │   │   ├── roadmap.py
│   │   │   ├── session.py
│   │   │   └── evidence.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── assessment.py
│   │   │   ├── profile.py
│   │   │   ├── roadmap.py
│   │   │   ├── session.py
│   │   │   ├── evidence.py
│   │   │   ├── checkpoint.py
│   │   │   ├── skill.py
│   │   │   └── support.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── assessment.py
│   │   │   ├── profile.py
│   │   │   ├── skill.py
│   │   │   ├── roadmap.py
│   │   │   ├── session.py
│   │   │   ├── evidence.py
│   │   │   ├── checkpoint.py
│   │   │   ├── resources.py
│   │   │   ├── doubt.py
│   │   │   └── tip.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── assessment_service.py
│   │   │   ├── normalization_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── parameter_service.py
│   │   │   ├── roadmap_service.py
│   │   │   ├── session_service.py
│   │   │   ├── validation_service.py
│   │   │   ├── rag_service.py
│   │   │   └── llm_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── jwt_handler.py
│   │       ├── clamping.py
│   │       └── hashing.py
│   ├── requirements.txt
│   └── .env
```

---

## SECTION 2 — DATA SCHEMA (Pydantic + SQLAlchemy)

### 2.1 Database Models (SQLAlchemy — backend/app/models/)

**user.py**
```python
# Table: users
id: UUID (PK)
email: str (UNIQUE, NOT NULL)
hashed_password: str (NOT NULL)
created_at: datetime (DEFAULT now())
status: str (DEFAULT "active")  # active | suspended | deleted
```

**cognitive_profile.py**
```python
# Table: cognitive_profiles
id: UUID (PK)
user_id: UUID (FK → users.id, NOT NULL)
version: int (DEFAULT 1, NOT NULL)
cognitive_capacity: Decimal(5,4)   # CHECK [0,1]
attention_stability: Decimal(5,4)  # CHECK [0,1]
learning_tolerance: Decimal(5,4)   # CHECK [0,1]
motor_baseline: Decimal(5,4)       # CHECK [0,1]
stress_resilience: Decimal(5,4)    # CHECK [0,1]
time_constraint: Decimal(5,4)      # CHECK [0,1]
raw_signals: JSON (NOT NULL)
created_at: datetime (DEFAULT now())
```

**learning_parameters.py**
```python
# Table: learning_parameters
id: UUID (PK)
profile_id: UUID (FK → cognitive_profiles.id)
skill_id: str

# Group A — Progression Control
difficulty_slope: Decimal(5,4)
phase_pacing: Decimal(5,4)
entry_phase_offset: Decimal(5,4)
repetition_intensity: Decimal(5,4)

# Group B — Session Structure
session_duration: Decimal(5,4)
micro_session_enabled: int        # 0 or 1
fatigue_threshold: Decimal(5,4)
break_frequency: Decimal(5,4)

# Group C — Cognitive Load
technique_density: Decimal(5,4)
concurrent_technique_limit: int   # 0–5
abstraction_level: Decimal(5,4)
instruction_granularity: Decimal(5,4)

# Group D — Validation
checkpoint_frequency: Decimal(5,4)
checkpoint_rigidity: Decimal(5,4)
error_tolerance_threshold: Decimal(5,4)
retry_limit: int                  # 0–5

# Group E — Practice Dynamics
drill_depth: Decimal(5,4)
variation_intensity: Decimal(5,4)
stress_exposure_rate: Decimal(5,4)
simulation_complexity: Decimal(5,4)

# Group F — Feedback
feedback_detail_level: Decimal(5,4)
correction_delay_window: Decimal(5,4)
hint_activation_threshold: Decimal(5,4)

# Group G — Motor
precision_requirement: Decimal(5,4)
speed_requirement: Decimal(5,4)
coordination_complexity: Decimal(5,4)

# Group H — Adaptive Meta
adaptation_sensitivity: Decimal(5,4)
risk_zone_trigger_level: Decimal(5,4)
regression_policy_strength: Decimal(5,4)
phase_transition_sensitivity: Decimal(5,4)
complexity_escalation_trigger: Decimal(5,4)
plateau_detection_threshold: Decimal(5,4)
stability_requirement_before_advance: Decimal(5,4)

created_at: datetime (DEFAULT now())
```

**roadmap.py**
```python
# Table: roadmaps
id: UUID (PK)
user_id: UUID (FK → users.id)
skill_id: str
profile_version: int
parameters_id: UUID (FK → learning_parameters.id)
structure: JSON   # full phase/competency/checkpoint/duration tree
status: str       # active | completed | abandoned
created_at: datetime
```

**session.py**
```python
# Table: sessions
id: UUID (PK)
roadmap_id: UUID (FK → roadmaps.id)
phase: str
technique_id: str
status: str           # pending | active | completed | failed
metrics_captured: JSON
protocol_violations: JSON
started_at: datetime
ended_at: datetime
```

**evidence.py**
```python
# Table: evidence
id: UUID (PK)
session_id: UUID (FK → sessions.id)
checkpoint_id: str
type: str             # numeric | artifact | behavioral_log
payload: JSON
artifact_url: str
validated: bool (DEFAULT False)
validation_result: JSON
created_at: datetime
```

---

### 2.2 Pydantic Schemas (backend/app/schemas/)

**auth.py**
```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str            # min 8 chars

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

**assessment.py**
```python
class RawSignalSubmit(BaseModel):
    level_id: str            # "executive_control" | "sustained_attention" |
                             # "learning_endurance" | "motor_precision" |
                             # "pressure_adaptation" | "time_structuring"
    accuracy: float          # 0.0–1.0
    mean_response_time: float
    response_time_variance: float
    performance_decay: float
    retry_depth: int
    dropout_depth_index: int
    recovery_slope: float
    available_hours_per_week: float | None   # level "time_structuring" only
    preferred_session_length: float | None   # level "time_structuring" only

class AssessmentCompleteResponse(BaseModel):
    profile_id: str
    cognitive_capacity: float
    attention_stability: float
    learning_tolerance: float
    motor_baseline: float
    stress_resilience: float
    time_constraint: float
    version: int
```

**profile.py**
```python
class ProfileVectorResponse(BaseModel):
    id: str
    user_id: str
    version: int
    cognitive_capacity: float
    attention_stability: float
    learning_tolerance: float
    motor_baseline: float
    stress_resilience: float
    time_constraint: float
    raw_signals: dict
    created_at: datetime
```

**skill.py**
```python
class GroundingProbeSubmit(BaseModel):
    skill_id: str
    recognition_score: float   # 0.0–1.0
    declarative_score: float   # 0.0–1.0
    confidence_bias: float     # 0.0–5.0 self-rated

class BaselineStateResponse(BaseModel):
    skill_id: str
    exposure_score: float
    declarative_knowledge: float
    confidence_bias: float
    adjusted_repetition_intensity: float
```

**roadmap.py**
```python
class RoadmapGenerateRequest(BaseModel):
    skill_id: str

class RoadmapGenerateResponse(BaseModel):
    job_id: str
    status: str = "queued"

class PhaseSchema(BaseModel):
    phase_slug: str
    competencies: list[str]
    techniques: list[str]
    checkpoints: list[str]
    estimated_hours: float
    status: str   # locked | active | completed

class RoadmapResponse(BaseModel):
    id: str
    skill_id: str
    profile_version: int
    phases: list[PhaseSchema]
    status: str
    created_at: datetime
```

**session.py**
```python
class SessionStartRequest(BaseModel):
    roadmap_id: str
    phase: str
    technique_id: str

class SessionStartResponse(BaseModel):
    session_id: str
    status: str = "active"

class SessionMetricsSubmit(BaseModel):
    session_id: str
    accuracy: float
    response_time: float
    error_count: int
    step_completion_log: list[str]

class SessionCompleteResponse(BaseModel):
    session_id: str
    status: str      # completed | failed
    violations: list[str]
```

**evidence.py**
```python
class EvidenceUploadResponse(BaseModel):
    evidence_id: str
    artifact_url: str
    type: str

class EvidenceRecord(BaseModel):
    id: str
    session_id: str
    checkpoint_id: str
    type: str
    validated: bool
    validation_result: dict | None
```

**checkpoint.py**
```python
class CheckpointValidateRequest(BaseModel):
    session_id: str
    checkpoint_id: str

class CheckpointValidateResponse(BaseModel):
    checkpoint_id: str
    passed: bool
    threshold_used: float
    actual_value: float
    detail: str
```

**support.py**
```python
class DoubtRequest(BaseModel):
    session_id: str
    phase: str
    technique_id: str
    user_query: str

class DoubtResponse(BaseModel):
    explanation: str
    sources_used: int

class TipResponse(BaseModel):
    tip: str
    trigger_reason: str   # "high_retry" | "high_decay" | "repeated_failure"

class ResourceItem(BaseModel):
    title: str
    url: str
    doc_type: str   # video | article | tool

class ResourceListResponse(BaseModel):
    resources: list[ResourceItem]
```

---

## SECTION 3 — API ROUTES

All routes prefix: `/api/v1`
Auth header on protected routes: `Authorization: Bearer <access_token>`

### 3.1 Auth Routes — `/api/v1/auth`

| Method | Path | Auth | Request Body | Response |
|---|---|---|---|---|
| POST | `/auth/register` | None | `RegisterRequest` | `201 { user_id, email }` |
| POST | `/auth/login` | None | `LoginRequest` | `200 TokenResponse` |
| POST | `/auth/refresh` | Cookie | None | `200 TokenResponse` |
| POST | `/auth/logout` | JWT | None | `200 { message }` |

### 3.2 Assessment Routes — `/api/v1/assessment`

| Method | Path | Auth | Request Body | Response |
|---|---|---|---|---|
| POST | `/assessment/start` | JWT | `{ user_id }` | `201 { session_id }` |
| POST | `/assessment/submit` | JWT | `RawSignalSubmit` | `200 { level_id, received: true }` |
| POST | `/assessment/complete` | JWT | `{ session_id }` | `201 AssessmentCompleteResponse` |
| GET | `/assessment/status` | JWT | — | `200 { levels_completed: [...], profile_active: bool }` |

### 3.3 Profile Routes — `/api/v1/profile`

| Method | Path | Auth | Request Body | Response |
|---|---|---|---|---|
| GET | `/profile/:user_id` | JWT | — | `200 ProfileVectorResponse` |
| GET | `/profile/:user_id/parameters` | JWT | — | `200 { all 32 learning parameters }` |
| GET | `/profile/:user_id/history` | JWT | — | `200 [ProfileVectorResponse, ...]` |

### 3.4 Skill Routes — `/api/v1/skill`

| Method | Path | Auth | Request Body | Response |
|---|---|---|---|---|
| GET | `/skill/list` | JWT | — | `200 [{ skill_id, name, complexity }]` |
| POST | `/skill/baseline` | JWT | `GroundingProbeSubmit` | `201 BaselineStateResponse` |
| GET | `/skill/:skill_id/baseline` | JWT | — | `200 BaselineStateResponse` |

### 3.5 Roadmap Routes — `/api/v1/roadmap`

| Method | Path | Auth | Request Body | Response |
|---|---|---|---|---|
| POST | `/roadmap/generate` | JWT | `RoadmapGenerateRequest` | `202 RoadmapGenerateResponse` |
| GET | `/roadmap/:user_id` | JWT | — | `200 RoadmapResponse` |
| GET | `/roadmap/:user_id/status` | JWT | — | `200 { status, job_id }` |
| PATCH | `/roadmap/:roadmap_id/abandon` | JWT | — | `200 { status: "abandoned" }` |

### 3.6 Session Routes — `/api/v1/session`

| Method | Path | Auth | Request Body | Response |
|---|---|---|---|---|
| POST | `/session/start` | JWT | `SessionStartRequest` | `201 SessionStartResponse` |
| POST | `/session/metrics` | JWT | `SessionMetricsSubmit` | `200 { received: true }` |
| POST | `/session/complete` | JWT | `{ session_id }` | `200 SessionCompleteResponse` |
| GET | `/session/:session_id` | JWT | — | `200 { session record }` |

### 3.7 Evidence Routes — `/api/v1/evidence`

| Method | Path | Auth | Request Body | Response |
|---|---|---|---|---|
| POST | `/evidence/upload` | JWT | `multipart/form-data` (file + session_id + checkpoint_id) | `201 EvidenceUploadResponse` |
| GET | `/evidence/:session_id` | JWT | — | `200 [EvidenceRecord, ...]` |

### 3.8 Checkpoint Routes — `/api/v1/checkpoint`

| Method | Path | Auth | Request Body | Response |
|---|---|---|---|---|
| POST | `/checkpoint/validate` | JWT | `CheckpointValidateRequest` | `200 CheckpointValidateResponse` |
| GET | `/checkpoint/:roadmap_id` | JWT | — | `200 [{ checkpoint_id, status, phase }]` |

### 3.9 Support Routes — `/api/v1`

| Method | Path | Auth | Request Body | Response |
|---|---|---|---|---|
| POST | `/doubt/ask` | JWT | `DoubtRequest` | `200 DoubtResponse` |
| GET | `/tip/:session_id` | JWT | — | `200 TipResponse` |
| GET | `/resources` | JWT | query: `skill_id, phase, technique_id` | `200 ResourceListResponse` |

---

## SECTION 4 — CRUD OPERATIONS PER ENTITY

### users

- **CREATE**: `POST /auth/register` → `auth_service.create_user()` → insert into `users`
- **READ**: Internal only via `dependencies.get_current_user()` from JWT
- **UPDATE**: `PATCH /auth/status` (admin only) → update `status` field
- **DELETE**: Soft delete — update `status = "deleted"`

### cognitive_profiles

- **CREATE**: `POST /assessment/complete` → `profile_service.build_profile()` → `normalization_service.normalize()` → insert new row (new version)
- **READ**: `GET /profile/:user_id` → fetch latest by `user_id ORDER BY version DESC LIMIT 1`
- **READ HISTORY**: `GET /profile/:user_id/history` → fetch all rows for user
- **UPDATE**: Not allowed. Each reassessment creates a new version row. Old rows are immutable.
- **DELETE**: Not applicable. Profiles are audit records.

### learning_parameters

- **CREATE**: Triggered automatically after `cognitive_profiles` insert → `parameter_service.derive_parameters()` → insert row linked to `profile_id`
- **READ**: `GET /profile/:user_id/parameters` → join with `cognitive_profiles` via `profile_id`
- **UPDATE**: Not allowed. Immutable after creation.
- **DELETE**: Not applicable.

### roadmaps

- **CREATE**: `POST /roadmap/generate` → queued job → `roadmap_service.generate()` → insert with full `structure` JSON
- **READ**: `GET /roadmap/:user_id` → fetch by `user_id WHERE status = "active"`
- **UPDATE**: `PATCH /roadmap/:roadmap_id/abandon` → set `status = "abandoned"`
- **DELETE**: Not applicable. Status change instead.

### sessions

- **CREATE**: `POST /session/start` → `session_service.start_session()` → insert with `status = "active"`
- **READ**: `GET /session/:session_id` → fetch by `id`
- **UPDATE (metrics)**: `POST /session/metrics` → append to `metrics_captured` JSON field
- **UPDATE (complete)**: `POST /session/complete` → `session_service.complete_session()` → set `status = "completed"` or `"failed"`, write `protocol_violations`, set `ended_at`
- **DELETE**: Not applicable.

### evidence

- **CREATE**: `POST /evidence/upload` → upload file to S3/R2 → insert record with `artifact_url`, `type`, `payload`, `validated = false`
- **READ**: `GET /evidence/:session_id` → fetch all evidence for session
- **UPDATE (validate)**: `POST /checkpoint/validate` → `validation_service.validate()` → set `validated = true`, write `validation_result`
- **DELETE**: Not applicable.

---

## SECTION 5 — FRONTEND PAGES — PURPOSE AND COMPONENT USAGE

### Page 1 — AuthPage.tsx

**Route**: `/` and `/login` and `/register`
**Purpose**: User registration and login.

**Components used**:
- `shadcn/ui`: `Card`, `CardContent`, `Input`, `Button`, `Label`, `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`
- `shared/LoadingSpinner.tsx`
- `shared/StatusPill.tsx`

**API connections**:
- `authApi.register(email, password)` → `POST /auth/register`
- `authApi.login(email, password)` → `POST /auth/login`

**Store interactions**:
- On success: `authStore.setToken(token)`, `authStore.setUser(user)`
- On success: navigate to `/dashboard`

---

### Page 2 — DashboardPage.tsx

**Route**: `/dashboard`
**Purpose**: Central hub. Shows active roadmap status, assessment completion status, and quick-action links.

**Components used**:
- `layout/AppShell.tsx` (wraps all authenticated pages)
- `layout/Sidebar.tsx`
- `layout/TopBar.tsx`
- `profile/ProfileSummaryCard.tsx` — shows 6 profile dimensions as summary
- `roadmap/RoadmapTimeline.tsx` — shows current active roadmap phases
- `shared/PageHeader.tsx`
- `shared/StatusPill.tsx`
- `shadcn/ui`: `Card`, `CardHeader`, `CardContent`, `Badge`, `Progress`, `Button`

**API connections**:
- `profileApi.getProfile(userId)` → `GET /profile/:user_id`
- `roadmapApi.getRoadmap(userId)` → `GET /roadmap/:user_id`
- `assessmentApi.getStatus()` → `GET /assessment/status`

**Store interactions**:
- Reads: `authStore.user`, `profileStore.profile`, `roadmapStore.roadmap`
- Sets: `profileStore.setProfile()`, `roadmapStore.setRoadmap()`

---

### Page 3 — AssessmentPage.tsx

**Route**: `/assessment`
**Purpose**: Hosts the 6-level cognitive assessment battery. One level active at a time. Displays questions, lives, timer, and level progress.

**Components used**:
- `assessment/AssessmentCard.tsx` — outer container per level
- `assessment/LivesIndicator.tsx` — renders 3 heart/life icons, dims on loss
- `assessment/QuestionBlock.tsx` — renders current question with answer options
- `assessment/TimerBar.tsx` — countdown progress bar per question
- `assessment/LevelBadge.tsx` — shows level name and completion state
- `shared/LoadingSpinner.tsx`
- `shared/StatusPill.tsx`
- `shadcn/ui`: `Card`, `Progress`, `Button`, `Badge`, `Alert`, `AlertDescription`

**API connections**:
- `assessmentApi.startSession()` → `POST /assessment/start`
- `assessmentApi.submitSignals(rawSignalSubmit)` → `POST /assessment/submit` — called after each level completes
- `assessmentApi.completeAssessment(sessionId)` → `POST /assessment/complete` — called after all 6 levels done
- `assessmentApi.getStatus()` → `GET /assessment/status` — on page load to resume

**Store interactions**:
- `assessmentStore.setCurrentLevel(levelId)`
- `assessmentStore.setLives(count)`
- `assessmentStore.markLevelComplete(levelId)`
- On `complete`: `profileStore.setProfile(response)` → navigate to `/profile`

---

### Page 4 — ProfilePage.tsx

**Route**: `/profile`
**Purpose**: Displays the full computed ProfileVector and all 32 derived learning parameters grouped by category.

**Components used**:
- `profile/ProfileRadarChart.tsx` — radar/spider chart of the 6 dimensions using recharts
- `profile/DimensionBar.tsx` — horizontal progress bar for each of 6 dimensions with label and value
- `profile/ProfileSummaryCard.tsx` — brief interpretation card per dimension
- `shared/PageHeader.tsx`
- `shadcn/ui`: `Card`, `CardHeader`, `CardContent`, `Separator`, `Badge`, `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`, `Table`, `TableRow`, `TableCell`, `TableHead`

**API connections**:
- `profileApi.getProfile(userId)` → `GET /profile/:user_id`
- `profileApi.getParameters(userId)` → `GET /profile/:user_id/parameters`

**Store interactions**:
- Reads: `profileStore.profile`, `profileStore.parameters`
- Sets both if not yet loaded

---

### Page 5 — SkillSelectPage.tsx

**Route**: `/skill/select`
**Purpose**: Shows available skills as selectable cards. User picks one to proceed to grounding.

**Components used**:
- `skill/SkillSelectorCard.tsx` — card per skill with name, domain, complexity indicator
- `shared/PageHeader.tsx`
- `shadcn/ui`: `Card`, `CardContent`, `Badge`, `Button`, `Input` (search filter)

**API connections**:
- `skillApi.listSkills()` → `GET /skill/list`

**Store interactions**:
- On skill select: store `skill_id` in `roadmapStore.setTargetSkill(skillId)` → navigate to `/skill/grounding`

---

### Page 6 — GroundingPage.tsx

**Route**: `/skill/grounding`
**Purpose**: Administers 3 lightweight grounding probes (recognition, familiarity, confidence) for the selected skill.

**Components used**:
- `skill/GroundingProbeForm.tsx` — step-through form with 3 probe types
- `skill/BaselineStateDisplay.tsx` — shows computed baseline after submission
- `shared/LoadingSpinner.tsx`
- `shadcn/ui`: `Card`, `CardContent`, `Button`, `Slider`, `RadioGroup`, `RadioGroupItem`, `Label`, `Progress`

**API connections**:
- `skillApi.submitBaseline(groundingProbeSubmit)` → `POST /skill/baseline`
- `skillApi.getBaseline(skillId)` → `GET /skill/:skill_id/baseline`

**Store interactions**:
- On success: store baseline in `roadmapStore.setBaseline(baselineState)` → navigate to `/roadmap/generate`

---

### Page 7 — RoadmapPage.tsx

**Route**: `/roadmap`
**Purpose**: Displays the fully generated roadmap with phases, competencies, techniques, and checkpoint statuses. Entry point to start sessions.

**Components used**:
- `roadmap/RoadmapTimeline.tsx` — vertical timeline of phases
- `roadmap/PhaseCard.tsx` — expandable card per phase showing competencies and techniques
- `roadmap/CheckpointItem.tsx` — individual checkpoint with pass/fail/pending status
- `roadmap/TechniqueTag.tsx` — badge chip per technique in a phase
- `shared/PageHeader.tsx`
- `shared/StatusPill.tsx`
- `shadcn/ui`: `Card`, `CardHeader`, `CardContent`, `Badge`, `Accordion`, `AccordionItem`, `AccordionTrigger`, `AccordionContent`, `Button`, `Progress`, `Separator`

**API connections**:
- `roadmapApi.getRoadmap(userId)` → `GET /roadmap/:user_id`
- `roadmapApi.generateRoadmap(skillId)` → `POST /roadmap/generate` (if not yet generated)
- `roadmapApi.getRoadmapStatus(userId)` → `GET /roadmap/:user_id/status` — polls job status if generation is async

**Store interactions**:
- Reads: `roadmapStore.roadmap`
- On phase card "Start Session" button: navigate to `/session` with `phase` and `technique_id` as route state

---

### Page 8 — SessionPage.tsx

**Route**: `/session`
**Purpose**: Executes one technique session. Displays step-by-step protocol, captures metrics in real time, and handles evidence upload.

**Components used**:
- `session/SessionProtocolStepper.tsx` — numbered step list; marks steps complete on user confirmation
- `session/MetricsCapturePanel.tsx` — displays live-captured accuracy, time, error count
- `session/EvidenceUploader.tsx` — file upload widget supporting image, pdf, video, text
- `session/SessionStatusBadge.tsx` — shows current session status pill
- `shared/LoadingSpinner.tsx`
- `shared/ErrorBoundary.tsx`
- `shadcn/ui`: `Card`, `CardContent`, `Button`, `Progress`, `Badge`, `Alert`, `AlertDescription`, `Separator`, `Input` (type=file hidden behind custom button)

**API connections**:
- `sessionApi.startSession(sessionStartRequest)` → `POST /session/start`
- `sessionApi.submitMetrics(sessionMetricsSubmit)` → `POST /session/metrics` — called on step completion and on interval
- `sessionApi.completeSession(sessionId)` → `POST /session/complete`
- `evidenceApi.uploadEvidence(formData)` → `POST /evidence/upload`
- `tipApi.getTip(sessionId)` → `GET /tip/:session_id` — called on repeated failure

**Store interactions**:
- `sessionStore.setSession(sessionStartResponse)`
- `sessionStore.setStatus(status)`
- On complete/fail: navigate back to `/roadmap` with updated phase status

---

### Page 9 — CheckpointPage.tsx

**Route**: `/checkpoint/:roadmapId`
**Purpose**: Shows all checkpoints for the active roadmap. Allows triggering validation for completed sessions.

**Components used**:
- `roadmap/CheckpointItem.tsx`
- `shared/PageHeader.tsx`
- `shared/StatusPill.tsx`
- `shadcn/ui`: `Card`, `CardContent`, `Table`, `TableRow`, `TableCell`, `TableHead`, `Button`, `Badge`, `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`

**API connections**:
- `checkpointApi.listCheckpoints(roadmapId)` → `GET /checkpoint/:roadmap_id`
- `checkpointApi.validateCheckpoint(checkpointValidateRequest)` → `POST /checkpoint/validate`
- `evidenceApi.getEvidence(sessionId)` → `GET /evidence/:session_id`

**Store interactions**:
- None persisted. Page fetches fresh on load.

---

### Page 10 — ResourcesPage.tsx

**Route**: `/resources`
**Purpose**: Displays curated learning resources filtered by current phase and technique. Read-only. Does not affect progress state.

**Components used**:
- `support/ResourceList.tsx` — renders list of resource cards with title, type badge, and external link
- `shared/PageHeader.tsx`
- `shadcn/ui`: `Card`, `CardContent`, `Badge`, `Button`, `Input` (filter), `Select`, `SelectTrigger`, `SelectContent`, `SelectItem`

**API connections**:
- `resourceApi.getResources(skillId, phase, techniqueId)` → `GET /resources`

**Store interactions**:
- Reads: `roadmapStore.roadmap` to pre-populate `skill_id` and `phase` query params

---

### Page 11 — DoubtPage.tsx

**Route**: `/doubt`
**Purpose**: Free-form query interface. User submits a doubt about current technique. RAG-grounded response displayed. Does not affect progress.

**Components used**:
- `support/DoubtPanel.tsx` — chat-style input and response area
- `support/TipCard.tsx` — shows last tip if session has failures
- `shared/PageHeader.tsx`
- `shared/LoadingSpinner.tsx`
- `shadcn/ui`: `Card`, `CardContent`, `Textarea`, `Button`, `Separator`, `ScrollArea`

**API connections**:
- `doubtApi.askDoubt(doubtRequest)` → `POST /doubt/ask`
- `tipApi.getTip(sessionId)` → `GET /tip/:session_id`

**Store interactions**:
- Reads: `sessionStore.session` to populate `session_id`, `phase`, `technique_id` automatically

---

## SECTION 6 — LAYOUT COMPONENTS

### AppShell.tsx
Wrapper for all authenticated pages. Renders `Sidebar`, `TopBar`, and `<Outlet />` (React Router). Checks `authStore.token`; if absent, redirects to `/`.

### Sidebar.tsx
Left navigation. Links to: Dashboard, Assessment, Profile, Skills, Roadmap, Resources, Doubt. Uses `shadcn/ui` `NavigationMenu` or custom nav with `Button variant="ghost"`. Highlights active route using `useLocation()`.

### TopBar.tsx
Top header. Shows app name, current user email from `authStore.user`, and logout button calling `authApi.logout()` then clearing `authStore`.

### ProtectedRoute.tsx
Wraps any route that requires auth. Reads `authStore.token`. If null, renders `<Navigate to="/" />`. Otherwise renders `<Outlet />`.

---

## SECTION 7 — STORE DEFINITIONS (Zustand)

### authStore.ts
```typescript
interface AuthStore {
  token: string | null
  user: { id: string; email: string } | null
  setToken: (token: string) => void
  setUser: (user: { id: string; email: string }) => void
  clearAuth: () => void
}
```

### assessmentStore.ts
```typescript
interface AssessmentStore {
  sessionId: string | null
  completedLevels: string[]      // level_id strings
  currentLevel: string | null
  lives: number
  profileActive: boolean
  setSessionId: (id: string) => void
  setCurrentLevel: (levelId: string) => void
  setLives: (count: number) => void
  markLevelComplete: (levelId: string) => void
  setProfileActive: (active: boolean) => void
}
```

### profileStore.ts
```typescript
interface ProfileStore {
  profile: ProfileVectorResponse | null
  parameters: Record<string, number> | null
  setProfile: (profile: ProfileVectorResponse) => void
  setParameters: (params: Record<string, number>) => void
}
```

### roadmapStore.ts
```typescript
interface RoadmapStore {
  targetSkillId: string | null
  baseline: BaselineStateResponse | null
  roadmap: RoadmapResponse | null
  setTargetSkill: (skillId: string) => void
  setBaseline: (baseline: BaselineStateResponse) => void
  setRoadmap: (roadmap: RoadmapResponse) => void
}
```

### sessionStore.ts
```typescript
interface SessionStore {
  session: SessionStartResponse | null
  status: string | null
  setSession: (session: SessionStartResponse) => void
  setStatus: (status: string) => void
  clearSession: () => void
}
```

---

## SECTION 8 — API CLIENT LAYER

### axiosClient.ts
```typescript
// Base axios instance
// baseURL: process.env.VITE_API_BASE_URL (e.g. "http://localhost:8000/api/v1")
// Request interceptor: attach Authorization header from authStore.token
// Response interceptor: on 401, clear authStore and redirect to "/"
```

### Each api file pattern (example: sessionApi.ts)
```typescript
import axiosClient from "./axiosClient"

export const sessionApi = {
  startSession: (body: SessionStartRequest) =>
    axiosClient.post("/session/start", body),

  submitMetrics: (body: SessionMetricsSubmit) =>
    axiosClient.post("/session/metrics", body),

  completeSession: (sessionId: string) =>
    axiosClient.post("/session/complete", { session_id: sessionId }),

  getSession: (sessionId: string) =>
    axiosClient.get(`/session/${sessionId}`),
}
```

The same pattern applies for every other api file — each function maps to exactly one route defined in Section 3.

---

## SECTION 9 — BACKEND SERVICE LAYER RESPONSIBILITIES

### normalization_service.py
Accepts raw signal dict. Applies all 9 normalization formulas with constants. Returns clamped normalized signal dict. Pure function, no DB access.

### profile_service.py
Accepts normalized signals. Applies 6 weighted sum formulas to produce `ProfileVector`. Clamps all outputs. Inserts new `cognitive_profiles` row. Returns profile object.

### parameter_service.py
Accepts `ProfileVector`. Applies all 32 parameter formulas across 8 groups. Clamps all outputs. Converts integer-typed params with `floor()` or `round()`. Inserts `learning_parameters` row. Returns parameter object.

### assessment_service.py
Orchestrates: receives `RawSignalSubmit` per level, stores in session buffer. On `complete`, calls `normalization_service` → `profile_service` → `parameter_service` in sequence. Returns `AssessmentCompleteResponse`.

### roadmap_service.py
Accepts `SkillResearchObject` + `SkillTemplate`. Generates roadmap structure deterministically with `temperature=0` LLM calls. Hashes output for fingerprint. Inserts `roadmaps` row. Returns roadmap.

### session_service.py
Manages session lifecycle: `start_session` inserts row with status `active`. `complete_session` checks `metrics_captured` for violations against parameter thresholds. Sets status to `completed` or `failed`. Writes `protocol_violations`.

### validation_service.py
Accepts `checkpoint_id` and `session_id`. Fetches linked `evidence` rows. For numeric evidence: compares `payload.value` against `checkpoint_rigidity`-derived threshold. Sets `validated` and writes `validation_result`. Returns pass/fail.

### llm_service.py
Wraps all LLM API calls. Enforces `temperature=0` on all structured calls. Validates JSON schema of response before returning. On schema failure: retry once, then return conservative default.

### rag_service.py
Runtime retrieval: takes query string + metadata filters (`skill_id`, `phase`, `technique_id`). Queries pgvector with embedding similarity. Returns top-k chunks for prompt injection.

---

## SECTION 10 — ROUTING STRUCTURE (React Router v6)

```
/                          → AuthPage (public)
/login                     → AuthPage (public)
/register                  → AuthPage (public)

Protected (ProtectedRoute wrapper):
/dashboard                 → DashboardPage
/assessment                → AssessmentPage
/profile                   → ProfilePage
/skill/select              → SkillSelectPage
/skill/grounding           → GroundingPage
/roadmap                   → RoadmapPage
/session                   → SessionPage
/checkpoint/:roadmapId     → CheckpointPage
/resources                 → ResourcesPage
/doubt                     → DoubtPage
```

---

## SECTION 11 — BACKEND MAIN REGISTRATION (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth, assessment, profile, skill,
    roadmap, session, evidence,
    checkpoint, resources, doubt, tip
)

app = FastAPI(title="SkillOS API", version="1.0.0")

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,       prefix="/api/v1/auth")
app.include_router(assessment.router, prefix="/api/v1/assessment")
app.include_router(profile.router,    prefix="/api/v1/profile")
app.include_router(skill.router,      prefix="/api/v1/skill")
app.include_router(roadmap.router,    prefix="/api/v1/roadmap")
app.include_router(session.router,    prefix="/api/v1/session")
app.include_router(evidence.router,   prefix="/api/v1/evidence")
app.include_router(checkpoint.router, prefix="/api/v1/checkpoint")
app.include_router(resources.router,  prefix="/api/v1")
app.include_router(doubt.router,      prefix="/api/v1")
app.include_router(tip.router,        prefix="/api/v1")
```

---

## SECTION 12 — ENVIRONMENT VARIABLES

**backend/.env**
```
DATABASE_URL=postgresql://user:password@localhost:5432/skillos
SECRET_KEY=<RS256 private key>
ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
S3_BUCKET_NAME=skillos-evidence
S3_REGION=ap-south-1
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
```

**frontend/.env**
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## SECTION 13 — KEY IMPLEMENTATION INVARIANTS

These are non-negotiable constraints derived from the specification that must be enforced in code, not just in design.

1. `normalization_service.py` must clamp every output: `max(0.0, min(1.0, value))` after every formula.
2. `n_dropout` formula: `1 - (dropout_depth_index / 10.0)` — not `dropout_depth_index / 10.0`.
3. `n_retry` formula: `1 - (retry_depth / 10.0)` — not `retry_depth / 10.0`.
4. `entry_phase_offset` = `0.5 * cognitive_capacity + 0.5 * learning_tolerance` — not `cognitive_capacity * 0.5` alone.
5. `risk_zone_trigger_level` = `1 - ((learning_tolerance + stress_resilience) / 2)` — inner average computed first.
6. All `ProfileVector` rows are immutable after insert. Reassessment creates a new row with `version + 1`.
7. All `LearningParameters` rows are immutable after insert.
8. All LLM calls in `llm_service.py` use `temperature=0` for structured output endpoints. RAG explanation calls use `temperature=0.2`.
9. `session_service.py` — a session that has any `protocol_violations` must be set to `status = "failed"`. No exceptions.
10. `validation_service.py` — `validated` is set to `true` only if evidence value meets or exceeds threshold. No partial credit logic.
11. Frontend: `ProtectedRoute.tsx` must check `authStore.token` synchronously before rendering any protected page.
12. Frontend: `SessionPage.tsx` must call `POST /session/metrics` at minimum on every completed step and also on a 30-second interval while session is `active`.
13. Roadmap generation must be async (job queue). `POST /roadmap/generate` returns `job_id`. Frontend polls `GET /roadmap/:user_id/status` until status is not `queued`.
14. Evidence uploads: backend must reject files exceeding 50MB and types outside `image/*, application/pdf, text/plain, video/mp4`.