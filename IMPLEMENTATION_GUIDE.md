# SkillOS Implementation Guide — Next Steps

This document outlines the remaining work to get SkillOS fully functional.

---

## 1. DATABASE INTEGRATION (Priority: HIGH)

### 1.1 Migrate Pydantic Schemas to Actual Endpoints

**Current State**: Schemas defined in spec but not wired  
**What to Do**:
- Map all 13 API endpoint definitions from flow.md Section 3 to FastAPI route handlers
- Each route should:
  1. Accept the specified request schema
  2. Call the appropriate service layer
  3. Return the specified response schema

**Example Pattern**:
```python
# backend/assessment/router.py
@router.post("/assessment/submit")
async def submit_signals(
    data: RawSignalSubmit,
    current_user: User = Depends(get_current_user),
) -> dict:
    # Call assessment_service.submit_signals()
    # Return { "level_id": str, "received": bool }
    pass
```

### 1.2 Implement SQLAlchemy Repository Layer

**Files to Create**:
```
backend/shared/db/repositories/
├── user_repository.py
├── profile_repository.py
├── parameter_repository.py
├── roadmap_repository.py
├── session_repository.py
├── evidence_repository.py
└── checkpoint_repository.py
```

**Pattern** (per repository):
```python
class UserRepository:
    async def create(self, email: str, hashed_password: str) -> User:
        # INSERT into users table
        
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        # SELECT from users WHERE id = user_id
        
    async def get_by_email(self, email: str) -> Optional[User]:
        # SELECT from users WHERE email = email
```

### 1.3 Wire Database Transactions

- Update service layer to use repositories
- Handle transaction rollback on error
- Implement soft deletes for user records

---

## 2. FRONTEND API INTEGRATION (Priority: HIGH)

### 2.1 Wire Views to API Calls

**Pattern** (in each view):
```typescript
useEffect(() => {
  const fetch = async () => {
    try {
      const res = await apiClient.getMethod();
      setData(res.data);
    } catch (err) {
      // Show error toast
    }
  };
  fetch();
}, []);
```

**Views Needing Wiring**:
- All 11 new views reference API clients but need actual integration
- Add error states and loading states
- Add React Query for data management

### 2.2 Add Component Wiring

**Missing**: All views use basic HTML; need shadcn/ui components:
```bash
# Install shadcn/ui
npx shadcn-ui@latest init

# Add components used in views
npx shadcn-ui@latest add card
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add slider
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add dialog
```

---

## 3. LLM INTEGRATION (Priority: MEDIUM)

### 3.1 Wire LLM Service to Actual API Calls

**Current**: `llm_service.py` has stub implementations  
**Needed**:

```python
# In backend/shared/config.py
llm_service = LLMService(
    provider=settings.llm_provider,  # "openai" or "anthropic"
    api_key=settings.openai_api_key or settings.anthropic_api_key
)
```

### 3.2 Test LLM Calls

```python
# Test structured response
schema = {"type": "object", "properties": {"explanation": {"type": "string"}}}
result = llm_service.generate_structured_response(
    prompt="Explain this...",
    schema=schema
)
```

---

## 4. RAG INTEGRATION (Priority: MEDIUM)

### 4.1 Set Up Embeddings + pgvector

**What to Do**:
1. Create skill documentation chunks (store in JSON files or S3)
2. Generate embeddings for each chunk via OpenAI `text-embedding-3-small`
3. Store embeddings + text in pgvector table
4. Implement similarity search

**Example SQL**:
```sql
CREATE TABLE skill_chunks (
    id UUID PRIMARY KEY,
    skill_id VARCHAR,
    phase VARCHAR,
    technique_id VARCHAR,
    content TEXT,
    embedding vector(1536),
    CONSTRAINT idx_embedding ON (embedding)
);
```

### 4.2 Complete RAG Retrieval

```python
# In rag_service.py
def retrieve_context(self, query: str, skill_id: str, ...):
    query_embedding = get_embedding(query)
    chunks = db.query(SkillChunk).filter(
        SkillChunk.embedding.cosine_distance(query_embedding) < 0.3
    ).limit(top_k).all()
    return chunks
```

---

## 5. EVIDENCE UPLOAD SYSTEM (Priority: MEDIUM)

### 5.1 Implement File Upload Endpoint

```python
# backend/evidence/router.py
@router.post("/evidence/upload")
async def upload_evidence(
    file: UploadFile,
    session_id: str = Form(...),
    checkpoint_id: str = Form(...),
) -> EvidenceUploadResponse:
    # 1. Validate file (size < 50MB, type in allowed list)
    # 2. Upload to S3/R2
    # 3. Create evidence record in DB
    # 4. Return artifact_url
```

### 5.2 Wire S3/R2 Storage

```python
# In backend/shared/storage/
async def upload_to_s3(
    file: UploadFile,
    session_id: str,
    checkpoint_id: str,
) -> str:
    # Uses boto3/aioboto3
    # Returns presigned URL or direct artifact_url
```

---

## 6. ROADMAP GENERATION JOB QUEUE (Priority: LOW)

### 6.1 Set Up Celery

```python
# backend/shared/queue/celery_app.py
from celery import Celery

celery_app = Celery(
    "skillos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

@celery_app.task
def generate_roadmap_task(
    user_id: str,
    skill_id: str,
    profile_id: str,
):
    # Call roadmap_service.generate()
    # Update job status
    # Return roadmap JSON
```

### 6.2 Update Endpoint to Queue Job

```python
@router.post("/roadmap/generate")
async def generate_roadmap(
    data: RoadmapGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    task = generate_roadmap_task.apply_async(args=[...])
    return {"job_id": task.id, "status": "queued"}
```

---

## 7. ASSESSMENT WORKFLOW (Priority: MEDIUM)

### 7.1 Complete Assessment 6-Level Flow

**Sequence**:
1. User starts assessment → `POST /assessment/start`
2. For each of 6 levels:
   - Display level-specific questions
   - Collect raw signals (accuracy, response time, etc.)
   - Submit via `POST /assessment/submit`
3. After all 6 complete → `POST /assessment/complete`
4. System returns `ProfileVector`

### 7.2 Implement Assessment Service

```python
class AssessmentService:
    async def start_session(self, user_id: str) -> AssessmentSession:
        # Create session record
        
    async def submit_level_signals(
        self,
        session_id: str,
        raw_signals: RawSignalSubmit,
    ) -> dict:
        # Store signals for this level
        
    async def complete_assessment(
        self,
        session_id: str,
    ) -> AssessmentCompleteResponse:
        # Call normalization_service
        # Call profile_service
        # Call parameter_service
        # Return ProfileVector
```

---

## 8. ERROR HANDLING & VALIDATION (Priority: HIGH)

### 8.1 Add Input Validation

All endpoints should validate:
- Email format
- Password strength
- Numeric ranges (0-1 for scores, etc.)
- File types and sizes

```python
from pydantic import Field, validator

class RawSignalSubmit(BaseModel):
    accuracy: float = Field(ge=0.0, le=1.0)
    mean_response_time: float = Field(gt=0)
    
    @validator("accuracy")
    def validate_accuracy(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("must be between 0 and 1")
        return v
```

### 8.2 User-Friendly Errors

Catch and format all errors:
```python
try:
    result = await operation()
except ValidationError as e:
    raise HTTPException(400, detail=str(e))
except DatabaseError as e:
    raise HTTPException(500, detail="Internal error")
```

---

## 🚀 QUICK START AFTER COMPLETING ABOVE

```bash
# 1. Set up environment
cp .env.example .env.local
direnv allow

# 2. Install dependencies
pip install -r backend/requirements.txt
npm install (in frontend/)

# 3. Run migrations
alembic upgrade head

# 4. Seed test data
python scripts/seed_skills.py

# 5. Start services
# Terminal 1: Backend
uvicorn backend.main:app --reload

# Terminal 2: Frontend
npm run dev

# Terminal 3: Celery (if roadmap queue enabled)
celery -A backend.shared.queue.celery_app worker --loglevel=info
```

---

## 📊 ESTIMATED EFFORT

| Task | Effort | Days |
|------|--------|------|
| Database Integration | 2-3 days | 2-3 |
| Frontend API Wiring | 2 days | 2 |
| LLM Service | 1 day | 1 |
| RAG Integration | 1-2 days | 1-2 |
| Evidence Upload | 1 day | 1 |
| Job Queue | 1 day | 1 |
| Testing + Polish | 2 days | 2 |
| **TOTAL** | | **10-13 days** |

---

## ✅ VALIDATION CHECKLIST

After implementing all sections:
- [ ] All 13 API endpoints return correct schemas
- [ ] All 11 frontend views load data successfully
- [ ] Assessment workflow generates ProfileVector
- [ ] Parameter derivation produces all 32 parameters
- [ ] Evidence upload + validation works
- [ ] Roadmap generation queues and completes
- [ ] RAG retrieval returns relevant chunks
- [ ] LLM generates doubt explanations
- [ ] Error handling covers all edge cases
- [ ] E2E test: register → assess → profile → skill → roadmap → session → complete

