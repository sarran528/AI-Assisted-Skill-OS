# Assessment Work Report

This document explains how each of the three main assessment endpoints work, how they utilize time, number of tests (levels), and how lives (retries/dropouts) are handled. It is based on the current backend implementation.

## Overview

The assessment process consists of three main endpoints:

1. **Start Assessment** (`/assessment/start`): Initializes a new assessment session for the user.
2. **Submit Assessment** (`/assessment/submit`): Submits raw data for a single assessment level (test).
3. **Complete Assessment** (`/assessment/complete`): Finalizes the session and computes the cognitive profile.

Each assessment session consists of up to 6 levels (tests), each with its own metrics and time constraints.

---

## 1. Start Assessment
- **Endpoint:** `POST /assessment/start`
- **Purpose:** Creates a new session for the user, returning a session ID and the list of levels to complete (1-6).
- **Time Utilization:** No time is measured at this stage; it simply records the session start.
- **Lives/Attempts:** Not relevant at this stage.

---

## 2. Submit Assessment
- **Endpoint:** `POST /assessment/submit`
- **Purpose:** Submits raw behavioral metrics and game performance for a single level.
- **Metrics Collected:**
  - `accuracy` (0-100%): Correct responses / Total questions.
  - `expected_time` (Seconds): Average time per response.
  - `latency_stability` (Seconds²): Variance of response times.
  - `decay_inverse` (0-1): Performance stability over the session.
  - `dropout` (0-10): Number of times the game was abandoned.
  - `retry` (0-10): Number of times the game was restarted.
  - `recovery` (0-1): Speed of correct responses after an error.
- **New Performance Tracking:**
  - `score` (Integer): Total points earned in the game level.
  - `lives_consumed` (0-3): Number of hearts/lives lost during the test.
  - `attempts_taken` (Integer): 1 (initial) + number of retries.
  - `time_taken` (Seconds): Total duration spent on this specific level.
- **Time Utilization:**
  - `time_taken` records the total clock time.
  - `expected_time` (RT) is used for cognitive speed calculation.
- **Lives/Attempts:**
  - Lives are consumed per error or timeout. If lives reach 0, the test ends early as a failure.
  - `attempts_taken` tracks persistence and learning efficiency.

---

## 3. Detailed Game Mechanics

Each of the 6 levels utilizes a unique game mechanic to stress-test specific cognitive functions.

| Level | Game Title | Cognitive Domain | Questions / Rounds | Timer Logic | Lives | Base Score | Speed Bonus |
|:---:|---|---|:---:|---|:---:|---|---|
| **1** | **Stroop Test** | Executive Control | 20 Questions | 3.0s → 1.5s per Q | 3 | +15 pts | +15 (if RT < 50% window) |
| **2** | **Flanker Test** | Sustained Attention | 10 Questions | 3.0s → 1.5s per Q | 3 | +25 pts | None |
| **3** | **Puzzle Game** | Working Memory | 3 Puzzles (2x2, 3x3, 4x4) | 30s / 60s / 120s | 3 | +20 pts | +0-20 (based on time left %) |
| **4** | **Dart Game** | Motor Baseline | 5 Levels (4 throws each) | Variable Speed (0.8x-3.8x) | 3 | +40 (Bullseye) | +15 (Near Hit) |
| **5** | **Pressure Test** | Stress Resilience | 10 Rounds | 8.0s → 2.5s per round | 3 | +30 pts | +20 (if RT < 50% window) |
| **6** | **Time Questions**| Time Constraint | 6 Questions | 10s per Q | 3 | +30 pts | None (Consistency check) |

---

## 4. Score Calculation Logic

The "Points" system serves as a gamified proxy for raw behavioral performance:

1. **Accuracy Base**: Points are primarily awarded for correct actions (matching the color, solving the puzzle, hitting the bullseye).
2. **Speed Bonus**: In cognitive speed tests (Stroop, Pressure), submitting a correct answer in the first 50% of the allowed time window doubles or significantly boosts the points.
3. **Consistency Bonus**: In the Puzzle game, points are scaled by the percentage of time remaining on the clock.
4. **Impact of Lives**: Losing a life does not deduct points already earned, but failing the test (0 lives) results in a total level score of 0, signaling a "dropout" event to the cognitive engine.

---

## 5. Complete Assessment
- **Endpoint:** `POST /assessment/complete`
- **Purpose:** Finalizes the session, aggregates all metrics, and computes the 6-dimension cognitive profile.
- **Aggregation:**
  - **Total Score**: The sum of points from all levels is stored in `assessment_sessions.score`.
  - **Normalization**: Raw metrics (latency, accuracy, lives consumed) are converted to [0,1] scores.
  - **Averaging**: Performance across all 6 levels is averaged to ensure a reliable "Cognitive Baseline."

---

## Summary Table

| Stage | Data Stored | Tests Involved | Performance Impact |
|---|---|---|---|
| **Start** | Session ID, User ID | 0 | N/A |
| **Submit** | Raw Metrics, Points, Lives | 1 Level | Tracks per-game accuracy & speed |
| **Complete**| Cognitive Profile, Final Score | 6 Levels | Finalizes learning roadmap |

---

## How the Core Profile is Calculated and Stored

### 1. Normalization
Raw metrics from each test are normalized to a [0,1] range using formulas that invert or scale values as needed. For example, `lives_consumed` is inverted so that losing 3 lives results in a lower resilience score than losing 0 lives.

### 2. Profile Vector Computation
For each level, normalized signals are combined into a 6-dimensional profile vector:
- **Cognitive Capacity**: Weighted sum of accuracy, latency, and stability.
- **Attention Stability**: Focuses on response time variance and performance decay.
- **Learning Tolerance**: Inversely weighted by retries and dropout events.
- **Motor Baseline**: Focused on precision and rhythm (primarily from Level 4).
- **Stress Resilience**: Based on recovery speed after errors and performance under tight timers.
- **Time Constraint**: Derived from Level 6's availability and consistency data.

### 3. Database Storage
- **`assessment_sessions`**: Stores raw per-level data and the total score.
- **`cognitive_profiles`**: Stores the final computed 6-dimension vector.
- **`learning_parameters`**: Stores 33 personalized parameters used to tune the learning engine.

---

## 6. Backend Database Storage Flow

### Where Data is Stored (In Order):

#### Stage 1: Submit Assessment (Per Level)
- **Endpoint Called**: `POST /assessment/submit`
- **Data Stored**: In `assessment_sessions.submissions` (JSON field) with:
  - `level`: 1-6
  - `metrics`: All 7 raw metrics
  - `time_constraint`: Hours and session preference
- **Result**: Session record updated with submitted level data
- **Database**: `assessment_sessions` table

#### Stage 2: Complete Assessment (After All 6 Levels)
- **Endpoint Called**: `POST /assessment/complete`
- **Prerequisites**: All 6 levels must be submitted first
- **Processing**:
  1. Fetch all 6 submissions from `assessment_sessions`
  2. Normalize each submission's raw metrics → [0,1] range
  3. Average normalized signals across all 6 levels
  4. Compute 6-dimension profile vector from averaged signals
  5. Derive 32+ learning parameters from profile
- **Data Stored**:
  - `cognitive_profiles` table: Final profile vector + averaged raw signals
  - `learning_parameters` table: 32+ derived parameters (linked to cognitive_profiles)
- **Returned to Frontend**: The complete profile with all 6 dimensions

---

## 7. Current Implementation Issues & Fixes

### Issue 1: Backend Connection Refused
**Error**: `GET http://localhost:8000/api/v1/assessment/status net::ERR_CONNECTION_REFUSED`

**Cause**: Backend server is not running.

**Fix**:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### Issue 2: Data Not Persisting After Submit
**Current Behavior**: Data submitted but not visible in database immediately.

**Expected Behavior**: 
- After `/submit` → Data should be visible in `assessment_sessions.submissions`
- After `/complete` → Computed profile should appear in `cognitive_profiles` table

**Why This Matters**:
- The backend is correctly storing raw submissions in JSON
- But the frontend may not be fetching the updated session status
- The `/assessment/status` endpoint should return the current session with all submissions

### Issue 3: Normalization & Learning Parameters Not Computed Until Complete
**Current Design**: 
- Normalization happens **only** when `/complete` is called
- Learning parameters are derived **only** when `/complete` is called

**This is Correct Because**:
- Single-level profiles are unreliable
- Averaging across all 6 levels smooths noise and provides a robust baseline
- Computing from aggregated data prevents premature parameter derivation

**To Verify This Is Working**:
1. Submit all 6 levels (via `/submit`)
2. Call `/complete` endpoint
3. Check `cognitive_profiles` table for the computed profile
4. Check `learning_parameters` table for the 32+ derived parameters

---

## 8. Integration Tests & Verification

### Integration Check Scripts

Three verification scripts have been implemented:

**Script 1: Configuration Checklist**
```bash
python scripts/check_assessment_setup.py
```
- Verifies project structure is complete
- Checks environment configuration
- Confirms all endpoints exist
- Validates frontend integration

**Script 2: Flow Integration Tests**
```bash
pytest tests/integration/test_assessment_flow.py -v
```
- Tests normalization produces [0,1] range
- Verifies profile vector computation
- Tests aggregation across 6 levels
- Validates session and submission storage
- Simulates complete flow end-to-end

**Script 3: API Integration Tests**
```bash
pytest tests/integration/test_assessment_api.py -v
```
- Tests backend connectivity on port 8000
- Verifies all 4 endpoints respond correctly
- Tests database connection
- Validates response schemas

---

## 9. Complete Debugging Checklist

### Before Starting Assessment
- [ ] Virtual environment active
- [ ] DATABASE_URL set to Supabase URL
- [ ] Backend running on `localhost:8000`
- [ ] Frontend running on `localhost:5173` (or configured port)

### During Assessment
- [ ] Session created in database after `/start`
- [ ] Each level submission updates `assessment_sessions`
- [ ] After 6 submissions: `completed_levels` = [1,2,3,4,5,6]
- [ ] All metrics within valid ranges

### After Completing All Levels
- [ ] `/assessment/complete` called successfully
- [ ] Profile computed with 6 dimensions
- [ ] All dimensions in [0,1] range
- [ ] Data stored in 3 tables:
  - `assessment_sessions` (marked completed)
  - `cognitive_profiles` (new record)
  - `learning_parameters` (32+ fields)

### Database Verification
Run these queries in Supabase console:
```sql
-- Verify session exists
SELECT session_id, user_id, status, completed_levels 
FROM assessment_sessions 
WHERE user_id = '<user_id>' 
ORDER BY created_at DESC LIMIT 1;

-- Verify profile exists
SELECT id, user_id, cognitive_capacity, attention_stability, 
       learning_tolerance, motor_baseline, stress_resilience, time_constraint
FROM cognitive_profiles 
WHERE user_id = '<user_id>' 
ORDER BY created_at DESC LIMIT 1;

-- Verify parameters exist
SELECT id, profile_id, difficulty_slope, phase_pacing, session_duration
FROM learning_parameters 
WHERE profile_id = '<profile_id>' 
LIMIT 1;
```

---

## 10. Implementation Files Created

### Documentation
- `docs/ASSESSMENT_INTEGRATION.md` - Complete integration guide with data flow, schemas, formulas
- `assessment_work_report.md` - This report (updated with full workflow)

### Test Scripts
- `tests/integration/test_assessment_flow.py` - Pure function tests (no HTTP)
- `tests/integration/test_assessment_api.py` - HTTP endpoint tests
- `scripts/check_assessment_setup.py` - Configuration verification
- `scripts/verify_assessment_integration.py` - Advanced verification script

---

## 11. Quick Start

```bash
# 1. Set environment
$env:DATABASE_URL = "postgresql://..."

# 2. Run configuration check
python scripts/check_assessment_setup.py

# 3. Start backend
python -m uvicorn backend.main:app --reload --port 8000

# 4. In another terminal, start frontend
cd frontend
npm run dev

# 5. Go through assessment in browser

# 6. Run integration tests
pytest tests/integration/ -v

# 7. Verify in Supabase console
# Run the database queries above
```

---

## Notes
- **Retries**: If a user chooses the "RETRY" option from the summary screen, their previous score for that level is replaced, but the `attempts_taken` count in the database increases.
- **Dropout Events**: Closing the browser or failing all lives counts as a dropout, which heavily penalizes the **Learning Tolerance** dimension.
- **High-Fidelity Tracking**: All timers are measured in milliseconds on the frontend and normalized to seconds on the backend for precision.
- **Normalization**: All metrics are normalized to [0,1] range before profile computation
- **Aggregation**: Only happens after all 6 levels are submitted
- **Database Storage**: Occurs automatically on `/complete` endpoint - no manual intervention needed

---

*This report is based on the system implementation as of April 2026.*
*All integration checks have been implemented and are ready for use.*
