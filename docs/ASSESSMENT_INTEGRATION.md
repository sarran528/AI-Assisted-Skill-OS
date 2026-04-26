# Assessment Integration - Complete Implementation Guide

## Overview

This document explains the complete assessment integration, including:
1. **Integration Check Scripts** - Verify everything is set up correctly
2. **How Data Flows** - From submission to database storage
3. **How to Debug** - If something isn't working
4. **Database Queries** - To verify data was stored

---

## Quick Start

### 1. Set Environment Variable
```powershell
$env:DATABASE_URL = "postgresql://user:password@host:port/database"
```

### 2. Run Configuration Check
```bash
python scripts/check_assessment_setup.py
```

This verifies:
- ✓ All project files exist
- ✓ Virtual environment is active
- ✓ All endpoints are configured
- ✓ Frontend and backend files are in place

### 3. Start Backend
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### 4. Start Frontend
```bash
cd frontend
npm run dev
```

### 5. Run Through Assessment
1. Navigate to Assessment view
2. Start assessment (POST /assessment/start)
3. Complete all 6 levels (POST /assessment/submit × 6)
4. Click "Compute Profile" (POST /assessment/complete)

### 6. Verify in Database
Run the queries below in Supabase console to verify data was stored.

---

## Integration Check Scripts

### Script 1: Setup Checklist
```bash
python scripts/check_assessment_setup.py
```

**What it checks:**
- Project structure is complete
- Virtual environment is active
- Database configuration
- Endpoints are configured
- Frontend files exist

**Output:** Configuration checklist with all items marked ✓ or ✗

---

### Script 2: Flow Integration Tests
```bash
pytest tests/integration/test_assessment_flow.py -v
```

**What it tests:**
1. Normalization produces [0,1] range values
2. Profile vector computation
3. Aggregation across 6 levels
4. Session storage
5. Submission storage
6. Database schema exists
7. Full flow simulation

**Requirements:**
- Backend does NOT need to be running
- Tests run pure functions (normalization, profile computation)
- Tests verify math/logic, not HTTP

---

### Script 3: API Integration Tests
```bash
pytest tests/integration/test_assessment_api.py -v
```

**What it tests:**
1. Backend is running on localhost:8000
2. POST /assessment/start works
3. POST /assessment/submit works
4. POST /assessment/complete works
5. GET /assessment/status works
6. Database connection is configured

**Requirements:**
- Backend MUST be running
- Valid auth token needed (currently mocked as "test-token")
- Tests use actual HTTP requests

---

### Script 4: Data Verification (Manual)
```bash
# In Supabase console, run these queries:

-- Check if assessment was created
SELECT session_id, user_id, status, completed_levels, score, created_at
FROM assessment_sessions
ORDER BY created_at DESC
LIMIT 1;

-- Check if profile was computed
SELECT id, user_id, version, cognitive_capacity, attention_stability, 
       learning_tolerance, motor_baseline, stress_resilience, time_constraint
FROM cognitive_profiles
ORDER BY created_at DESC
LIMIT 1;

-- Check if parameters were derived
SELECT id, profile_id, skill_id, difficulty_slope, phase_pacing,
       entry_phase_offset, repetition_intensity
FROM learning_parameters
ORDER BY created_at DESC
LIMIT 1;
```

---

## Complete Data Flow

### Phase 1: Session Initialization
```
User clicks "Start Assessment"
         ↓
POST /assessment/start
         ↓
Backend creates AssessmentSession
         ↓
Database: INSERT INTO assessment_sessions 
  (id, session_id, user_id, status, submissions, completed_levels)
         ↓
Returns: { session_id, levels: [1,2,3,4,5,6], status: "started" }
```

### Phase 2: Level Submission (Repeated 6 times)
```
User completes Level 1
         ↓
POST /assessment/submit
  {
    session_id: "...",
    level: 1,
    metrics: { accuracy, expected_time, latency_stability, ... },
    time_constraint: { available_hours_per_week, preferred_session_length }
  }
         ↓
Backend:
  1. Validates input
  2. Retrieves AssessmentSession
  3. Adds submission to session.submissions[level]
  4. Updates completed_levels list
         ↓
Database: UPDATE assessment_sessions 
  SET submissions = {..., "1": {metrics, constraints}},
      completed_levels = [1, 2, ...],
      updated_at = NOW()
         ↓
Returns: { session_id, level: 1, status: "in_progress" }
```

### Phase 3: Assessment Completion & Profile Computation
```
User clicks "Compute Profile"
         ↓
POST /assessment/complete
  {
    session_id: "...",
    completed_levels: [1,2,3,4,5,6]
  }
         ↓
Backend Processing:
  
  1. Fetch AssessmentSession with all 6 submissions
  
  2. For each submission:
     → normalize_all(metrics, time_constraint)
     → Converts to [0,1] range
     → Produces 9 normalized signals per level
  
  3. Aggregate across all 6 levels:
     → Average normalized signals
     → Result: Single aggregated signal vector
  
  4. Compute profile vector:
     → Weighted combination of aggregated signals
     → 6 dimensions: [cognitive_capacity, attention_stability, 
                      learning_tolerance, motor_baseline, 
                      stress_resilience, time_constraint]
  
  5. Derive learning parameters:
     → 32+ parameters from profile dimensions
     → Skill-specific tuning parameters
  
  6. Store results:
     → INSERT INTO cognitive_profiles (profile_vector, raw_signals)
     → INSERT INTO learning_parameters (32+ fields)
     → UPDATE assessment_sessions SET status = "completed"
         ↓
Returns: {
  profile_id,
  user_id,
  version,
  cognitive_capacity: 0.7823,
  attention_stability: 0.6512,
  learning_tolerance: 0.8943,
  motor_baseline: 0.5421,
  stress_resilience: 0.7234,
  time_constraint: 0.6543
}
         ↓
Frontend receives profile → Displays to user
```

---

## Database Schema

### Table 1: assessment_sessions
Stores per-session data and raw submissions.

```sql
CREATE TABLE assessment_sessions (
  id STRING PRIMARY KEY,
  session_id STRING UNIQUE NOT NULL,
  user_id STRING NOT NULL FOREIGN KEY (users.id),
  status STRING DEFAULT 'in_progress',  -- 'in_progress', 'completed'
  submissions JSONB,  -- { "1": {...}, "2": {...}, ... }
  completed_levels JSONB,  -- [1, 2, 3, 4, 5, 6]
  score INTEGER DEFAULT 0,  -- Total points across all levels
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**What gets stored:**
- All raw metrics from each level (in submissions JSON)
- Which levels have been completed
- Session status
- Total score

**Lifecycle:**
- Created on /start
- Updated on each /submit
- Marked "completed" on /complete

---

### Table 2: cognitive_profiles
Stores the final 6-dimension cognitive profile.

```sql
CREATE TABLE cognitive_profiles (
  id STRING PRIMARY KEY,
  user_id STRING NOT NULL FOREIGN KEY (users.id),
  version INTEGER DEFAULT 1,
  cognitive_capacity NUMERIC(6,5),     -- 0.7823
  attention_stability NUMERIC(6,5),    -- 0.6512
  learning_tolerance NUMERIC(6,5),     -- 0.8943
  motor_baseline NUMERIC(6,5),         -- 0.5421
  stress_resilience NUMERIC(6,5),      -- 0.7234
  time_constraint NUMERIC(6,5),        -- 0.6543
  raw_signals JSON,  -- All 9 normalized signals
  assessment_metadata JSON,  -- Additional context
  created_at TIMESTAMP
);
```

**What gets stored:**
- 6 profile dimensions (each 0.0-1.0)
- Raw normalized signals (for audit/replay)
- Metadata about the assessment

**Created on:** /complete endpoint only

---

### Table 3: learning_parameters
Stores 32+ personalized learning parameters.

```sql
CREATE TABLE learning_parameters (
  id STRING PRIMARY KEY,
  profile_id STRING NOT NULL FOREIGN KEY (cognitive_profiles.id),
  skill_id STRING,  -- Which skill this is for
  
  -- Group A: Difficulty (4 params)
  difficulty_slope NUMERIC(6,5),
  phase_pacing NUMERIC(6,5),
  entry_phase_offset NUMERIC(6,5),
  repetition_intensity NUMERIC(6,5),
  
  -- Group B: Session Structure (4 params)
  session_duration NUMERIC(6,5),
  micro_session_enabled SMALLINT,
  fatigue_threshold NUMERIC(6,5),
  break_frequency NUMERIC(6,5),
  
  -- Group C: Technique Management (4 params)
  technique_density NUMERIC(6,5),
  concurrent_technique_limit SMALLINT,
  abstraction_level NUMERIC(6,5),
  instruction_granularity NUMERIC(6,5),
  
  -- ... (20+ more parameters)
  
  created_at TIMESTAMP
);
```

**What gets stored:**
- 32+ parameters derived from the cognitive profile
- Used to personalize learning roadmap
- Skill-specific tuning

**Created on:** /complete endpoint (after profile computed)

---

## Normalization Formulas

Each metric is converted to [0,1] range:

```
n_accuracy = accuracy / 100
  Example: 85% → 0.85

n_latency = 1 - (expected_time / 10)
  Example: 5 seconds → 1 - 0.5 = 0.5
  (Faster = Higher score)

n_latency_stability = 1 - (variance / 25)
  Example: 10 variance → 1 - 0.4 = 0.6
  (Lower variance = Higher score)

n_decay_inverse = decay_inverse / 1
  Example: 0.75 → 0.75
  (Pass-through, already normalized)

n_dropout = 1 - (dropout / 10)
  Example: 2 dropouts → 1 - 0.2 = 0.8
  (Fewer dropouts = Higher score)

n_retry = 1 - (retry / 10)
  Example: 1 retry → 1 - 0.1 = 0.9
  (Fewer retries = Higher score)

n_recovery = recovery / 1
  Example: 0.8 → 0.8
  (Pass-through)

n_hours = available_hours / 40
  Example: 20 hours → 0.5

n_session_pref = session_length / 120
  Example: 60 minutes → 0.5
```

---

## Profile Vector Computation

Each dimension is weighted sum of normalized signals:

```
cognitive_capacity = 0.35*n_accuracy + 0.20*n_latency + 
                     0.15*n_latency_stability + 0.10*n_decay_inverse + 
                     0.20*n_recovery

attention_stability = 0.50*n_latency_stability + 0.50*n_decay_inverse

learning_tolerance = 0.40*n_dropout + 0.40*n_retry + 0.20*n_recovery

motor_baseline = 0.60*n_latency + 0.40*n_latency_stability

stress_resilience = 0.60*n_recovery + 0.40*n_decay_inverse

time_constraint = 0.70*n_hours + 0.30*n_session_pref
```

Result: Each dimension in [0, 1] range

---

## Troubleshooting

### Issue: Connection Refused
```
Error: ERR_CONNECTION_REFUSED on localhost:8000
```

**Fix:**
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

---

### Issue: DATABASE_URL Not Set
```
Error: Attempting to connect to PostgreSQL but DATABASE_URL not found
```

**Fix:**
```powershell
$env:DATABASE_URL = "postgresql://user:password@host:5432/database"
```

Get your Supabase URL from: https://supabase.com → Project Settings → Database

---

### Issue: Data Not Showing in Database

**Debug Checklist:**

1. ✓ Backend running? `http://localhost:8000/docs`
2. ✓ Assessment completed successfully?
3. ✓ DATABASE_URL set to Supabase?
4. ✓ Run database query to check:

```sql
SELECT COUNT(*) FROM assessment_sessions;
SELECT COUNT(*) FROM cognitive_profiles;
SELECT COUNT(*) FROM learning_parameters;
```

5. ✓ Check recent errors in backend logs
6. ✓ Verify user_id matches between sessions and profiles

---

### Issue: Profile Not Computing

**Debug:**

1. Check that all 6 levels are submitted:
```sql
SELECT completed_levels FROM assessment_sessions 
WHERE session_id = '...';
-- Should show: [1, 2, 3, 4, 5, 6]
```

2. Check /assessment/complete request:
```json
{
  "session_id": "...",
  "completed_levels": [1, 2, 3, 4, 5, 6]
}
```

3. Check backend logs for normalization errors

4. Verify metrics are in valid ranges

---

## Testing Commands

### Run All Integration Tests
```bash
pytest tests/integration/ -v
```

### Run Flow Tests Only
```bash
pytest tests/integration/test_assessment_flow.py -v
```

### Run API Tests Only
```bash
pytest tests/integration/test_assessment_api.py -v -s
# -s shows print output
```

### Run Single Test
```bash
pytest tests/integration/test_assessment_flow.py::TestAssessmentFlow::test_normalization_produces_valid_range -v
```

---

## Manual Testing in Postman

1. Create request: POST http://localhost:8000/api/v1/assessment/start
2. Headers: `Authorization: Bearer test-token`
3. Send → Get session_id
4. Create request: POST http://localhost:8000/api/v1/assessment/submit
5. Body: Submit level with metrics
6. Create request: POST http://localhost:8000/api/v1/assessment/complete
7. Body: Include session_id and completed_levels
8. Response should contain 6-dimension profile

---

## Summary

**✓ What was implemented:**
- 3 integration check scripts
- 2 pytest test suites (flow + API)
- Complete data flow documentation
- Database schema definitions
- Normalization formulas
- Troubleshooting guide

**✓ To verify everything works:**
1. Run: `python scripts/check_assessment_setup.py`
2. Start backend: `python -m uvicorn backend.main:app --reload`
3. Go through assessment in UI
4. Run: `pytest tests/integration/ -v`
5. Query database to verify data stored

**✓ Expected outcome:**
- Assessment sessions stored in `assessment_sessions` table
- Profiles stored in `cognitive_profiles` table
- Parameters stored in `learning_parameters` table
- All data retrievable and displayable

---

*Last updated: April 2026*
