## 1. Page → Card Mapping (UI Structure)

Each page corresponds to a **specific system object**. Cards are UI representations of those objects.

---

### A. Home Page (Pre-Skill State)

**Card: CreateSkillCard**

* Bound to: `ProfileVector exists AND SkillRoadmap == null`
* API:

  * `GET /profile/status`
  * `POST /skill/init`

---

### B. Skill Initialization Page

**Cards:**

1. SkillSelectionCard

   * API: `GET /skills/templates`

2. GroundingProbeCard

   * API:

     * `GET /skill/{id}/grounding`
     * `POST /skill/{id}/grounding/submit`

3. RoadmapGenerationCard

   * API:

     * `POST /skill/{id}/roadmap/generate`
     * `GET /skill/{id}/roadmap/status`

---

### C. Dashboard (Post-Roadmap)

**Cards:**

1. ProfileSummaryCard

   * API: `GET /profile/vector`

2. RoadmapSnapshotCard

   * API: `GET /skill/{id}/roadmap`

3. CurrentPhaseCard

   * API: `GET /skill/{id}/phase/current`

4. PrimaryActionCard

   * API: derived from phase + checkpoint state

---

### D. Execution Page

**Cards:**

1. TechniqueProtocolCard

   * API: `GET /skill/{id}/technique/current`

2. SessionExecutionCard

   * API:

     * `POST /session/start`
     * `POST /session/submit`

3. MetricsCard

   * API: `GET /session/{id}/metrics`

---

### E. Checkpoint Page

**Cards:**

1. CheckpointCard

   * API: `GET /skill/{id}/checkpoint/current`

2. EvidenceSubmissionCard

   * API: `POST /evidence/submit`

3. ValidationResultCard

   * API: `GET /evidence/{id}/status`

---

### F. Assistant Panel

**Card: AssistantCard**

* API:

  * `POST /assistant/query`
* Input:

  * question
  * phase_id
  * context

Constraint from system:
Assistant cannot access validation endpoints 

---

### G. Resource Page

**Card: ResourceCard**

* API:

  * `GET /resources?phase_id=&skill_id=`

---

### H. History Page

**Cards:**

1. EvidenceHistoryCard

   * API: `GET /evidence/history`

2. LevelProgressCard

   * API: `GET /skill/{id}/progress`

---

## 2. Core API Layer Structure

---

### A. Profile Service

```http
GET  /profile/vector
GET  /profile/status
```

---

### B. Skill Service

```http
GET  /skills/templates
POST /skill/init
GET  /skill/{id}
```

---

### C. Grounding Service

```http
GET  /skill/{id}/grounding
POST /skill/{id}/grounding/submit
```

---

### D. Roadmap Service

```http
POST /skill/{id}/roadmap/generate
GET  /skill/{id}/roadmap
GET  /skill/{id}/phase/current
```

---

### E. Execution Service

```http
POST /session/start
POST /session/submit
GET  /session/{id}/metrics
```

---

### F. Validation Service

```http
GET  /skill/{id}/checkpoint/current
POST /evidence/submit
GET  /evidence/{id}/status
```

---

### G. Assistant Service (RAG Only)

```http
POST /assistant/query
```

---

### H. Resource Service

```http
GET /resources
```

---

## 3. Data Flow Binding

Every card must map to exactly one backend object:

| Card           | Backend Object    |
| -------------- | ----------------- |
| ProfileSummary | ProfileVector     |
| Roadmap        | SkillRoadmap      |
| Phase          | Phase             |
| Technique      | TechniqueProtocol |
| Session        | TechniqueSession  |
| Evidence       | EvidenceObject    |

From architecture: all objects are persisted and versioned 

---

## 4. Control Rules

* No card calls multiple unrelated APIs
* No page mixes different pipeline stages
* UI state = backend state only
* No derived logic in frontend (orchestration layer owns it)

---

## 5. Minimal Frontend Routing

```plaintext
/           → Home
/skill/init → Skill Setup
/dashboard  → Roadmap Overview
/execute    → Session Execution
/checkpoint → Validation
/resources  → Learning Resources
/history    → Progress History
```

---

## 6. Architectural Constraint

Frontend = display + input only
All decisions enforced by:

* Orchestration layer
* Validation layer

As defined in system architecture 

---

## Result

You now have:

* Page-to-card mapping
* Card-to-API binding
* API segmentation
* Data ownership clarity

This is sufficient to implement full UI + backend integration without ambiguity.
