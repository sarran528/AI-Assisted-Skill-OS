**SkillOS**

Database Schema & Authentication System

*Phase A --- Infrastructure Specification \| Build Step 1 & 3*

**Part 1 --- Database Schema**

All tables live in a single PostgreSQL database with the pgvector
extension enabled. Every table uses UUID primary keys, TIMESTAMPTZ for
all timestamps, and JSONB for structured flexible payloads. All major
objects are immutable after creation and versioned with a new row on
update.

**1.1 Prerequisites**

Run once on a fresh database before any migration:

> CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
>
> CREATE EXTENSION IF NOT EXISTS vector;
>
> CREATE EXTENSION IF NOT EXISTS pg_trgm; \-- for text search on skill
> names
>
> *pgvector must be installed on the PostgreSQL instance before running
> migrations. Version requirement: pgvector \>= 0.5.0 for HNSW index
> support. The vector dimension (1536 for OpenAI text-embedding-3-small)
> must match the embedding model exactly --- changing it requires
> dropping and recreating the vector column and re-indexing all chunks.*

**1.2 Table: users**

Root identity table. One row per registered user. No learning data
stored here --- only authentication identity.

  ---------------------------------------------------------------------------
  **Column**       **Type**        **Constraints**          **Description**
  ---------------- --------------- ------------------------ -----------------
  id               UUID            PK DEFAULT               Primary key
                                   uuid_generate_v4()       

  email            VARCHAR(255)    UNIQUE NOT NULL          Login identifier
                                                            --- lowercased
                                                            before insert

  password_hash    TEXT            NOT NULL                 bcrypt hash, cost
                                                            factor 12

  status           VARCHAR(32)     NOT NULL DEFAULT         active \|
                                   \'active\'               suspended \|
                                                            deleted

  created_at       TIMESTAMPTZ     NOT NULL DEFAULT now()   Account creation
                                                            time

  updated_at       TIMESTAMPTZ     NOT NULL DEFAULT now()   Last profile
                                                            update
  ---------------------------------------------------------------------------

**Indexes**

  ------------------------------------------------------------------------
  **Index name**        **Column(s)**    **Purpose**
  --------------------- ---------------- ---------------------------------
  users_email_idx       email            Unique lookup on login --- email
                                         is unique but index accelerates
                                         auth queries

  users_status_idx      status           Filter active/suspended users in
                                         admin queries
  ------------------------------------------------------------------------

**Constraints & Rules**

  -----------------------------------------------------------------------
  **Constraint**         **Definition**
  ---------------------- ------------------------------------------------
  **Email format**       Validated at application layer before insert.
                         Stored lowercase. No duplicates.

  **Password**           Never stored in plaintext. bcrypt with cost=12.
                         Hash verified at application layer only.

  **Soft delete**        status=\'deleted\' --- row is never physically
                         deleted. Foreign keys from other tables remain
                         intact.

  **updated_at**         Maintained via a PostgreSQL trigger: SET
                         updated_at = now() ON UPDATE.
  -----------------------------------------------------------------------

**1.3 Table: refresh_tokens**

Tracks issued refresh tokens for revocation and rotation. One row per
active refresh token per user.

  -------------------------------------------------------------------------------
  **Column**      **Type**      **Constraints**      **Description**
  --------------- ------------- -------------------- ----------------------------
  id              UUID          PK DEFAULT           Primary key
                                uuid_generate_v4()   

  user_id         UUID          FK users.id NOT NULL Token owner

  token_hash      TEXT          NOT NULL             SHA-256 hash of the raw
                                                     token --- never store raw

  jti             UUID          NOT NULL UNIQUE      JWT ID claim --- used for
                                                     access token revocation
                                                     lookup

  issued_at       TIMESTAMPTZ   NOT NULL DEFAULT     When the token was issued
                                now()                

  expires_at      TIMESTAMPTZ   NOT NULL             Absolute expiry --- 30 days
                                                     from issued_at

  revoked_at      TIMESTAMPTZ   NULLABLE             Set on logout or rotation.
                                                     NULL = still valid

  ip_address      INET          NULLABLE             Client IP at issuance ---
                                                     for anomaly detection

  user_agent      TEXT          NULLABLE             Browser/client string at
                                                     issuance
  -------------------------------------------------------------------------------

**Indexes**

  ------------------------------------------------------------------------
  **Index name**        **Column(s)**    **Purpose**
  --------------------- ---------------- ---------------------------------
  rt_user_id_idx        user_id          Fetch all tokens for a user on
                                         logout-all

  rt_token_hash_idx     token_hash       Validate incoming refresh token
                                         by hash lookup

  rt_jti_idx            jti              Revocation check for access
                                         tokens by jti claim

  rt_expires_idx        expires_at       Cleanup job deletes rows WHERE
                                         expires_at \< now()
  ------------------------------------------------------------------------

> *Cleanup: a scheduled job (cron or Celery beat) runs DELETE FROM
> refresh_tokens WHERE expires_at \< now() AND revoked_at IS NOT NULL
> daily. This prevents unbounded table growth while preserving audit
> trail for recently revoked tokens.*

**1.4 Table: revoked_access_tokens**

Short-lived blocklist for access tokens that have been explicitly
revoked before their natural expiry (e.g. force logout). Kept lean ---
entries are deleted once the token would have expired anyway.

  ------------------------------------------------------------------------
  **Column**      **Type**      **Constraints**    **Description**
  --------------- ------------- ------------------ -----------------------
  jti             UUID          PK                 JWT ID from the access
                                                   token being revoked

  user_id         UUID          FK users.id NOT    Owner --- enables
                                NULL               revoke-all-for-user
                                                   queries

  revoked_at      TIMESTAMPTZ   NOT NULL DEFAULT   Revocation timestamp
                                now()              

  expires_at      TIMESTAMPTZ   NOT NULL           Original token expiry
                                                   --- delete row after
                                                   this passes
  ------------------------------------------------------------------------

> *Auth middleware checks this table on every protected request. Query:
> SELECT 1 FROM revoked_access_tokens WHERE jti = \$1 AND expires_at \>
> now(). Redis cache recommended in front of this query at scale ---
> cache miss falls through to DB.*

**1.5 Table: cognitive_profiles**

Stores the output of the assessment pipeline. Immutable after creation
--- reassessment produces a new row with an incremented version number.
The active profile is the row with the highest version for a given user.

  ----------------------------------------------------------------------------------
  **Column**            **Type**       **Constraints**      **Description**
  --------------------- -------------- -------------------- ------------------------
  id                    UUID           PK DEFAULT           Primary key
                                       uuid_generate_v4()   

  user_id               UUID           FK users.id NOT NULL Profile owner

  version               INT            NOT NULL DEFAULT 1   Incremented per
                                                            reassessment. Never
                                                            updated in place.

  cognitive_capacity    NUMERIC(6,5)   NOT NULL CHECK       Weighted composite:
                                       (value BETWEEN 0 AND 0.35\*acc +
                                       1)                   0.20\*latency + \...

  attention_stability   NUMERIC(6,5)   NOT NULL CHECK       Sustained focus
                                       (value BETWEEN 0 AND dimension
                                       1)                   

  learning_tolerance    NUMERIC(6,5)   NOT NULL CHECK       Retry/dropout/recovery
                                       (value BETWEEN 0 AND composite
                                       1)                   

  motor_baseline        NUMERIC(6,5)   NOT NULL CHECK       Motor precision and
                                       (value BETWEEN 0 AND latency stability
                                       1)                   

  stress_resilience     NUMERIC(6,5)   NOT NULL CHECK       Recovery under pressure
                                       (value BETWEEN 0 AND composite
                                       1)                   

  time_constraint       NUMERIC(6,5)   NOT NULL CHECK       0.70\*n_hours +
                                       (value BETWEEN 0 AND 0.30\*n_session_pref
                                       1)                   

  raw_signals           JSONB          NOT NULL             All 9 normalized signals
                                                            stored for auditability

  assessment_metadata   JSONB          NOT NULL DEFAULT     Level completion flags,
                                       \'{}\'               attempt counts, session
                                                            timestamps

  created_at            TIMESTAMPTZ    NOT NULL DEFAULT     Profile creation time
                                       now()                --- immutable
  ----------------------------------------------------------------------------------

**Indexes**

  ------------------------------------------------------------------------
  **Index name**        **Column(s)**    **Purpose**
  --------------------- ---------------- ---------------------------------
  cp_user_id_idx        user_id          Fetch all profile versions for a
                                         user

  cp_user_version_idx   (user_id,        Unique --- prevents duplicate
                        version)         version numbers per user. Also
                                         used to fetch latest: ORDER BY
                                         version DESC LIMIT 1

  cp_created_at_idx     created_at       Time-range queries on assessment
                                         history
  ------------------------------------------------------------------------

**raw_signals JSONB schema**

The raw_signals column stores the exact normalized signal values used to
compute the ProfileVector:

> { \"n_accuracy\": 0.84, \"n_latency\": 0.71, \"n_latency_stability\":
> 0.66,
>
> \"n_decay_inverse\": 0.78, \"n_dropout\": 0.90, \"n_retry\": 0.85,
>
> \"n_recovery\": 0.73, \"n_hours\": 0.50, \"n_session_pref\": 0.625 }

**assessment_metadata JSONB schema**

> { \"levels_completed\": \[1,2,3,4,5,6\],
>
> \"level_attempts\": { \"1\": 2, \"2\": 1, \"3\": 1, \"4\": 1, \"5\":
> 1, \"6\": 1 },
>
> \"profile_activated_at\": \"2025-01-15T10:32:00Z\" }

  -----------------------------------------------------------------------
  **Constraint**         **Definition**
  ---------------------- ------------------------------------------------
  **Immutability**       No UPDATE on this table. New assessment = new
                         row with version = previous_max + 1.

  **CHECK constraints**  All 6 dimension columns have CHECK (column_name
                         BETWEEN 0 AND 1). Application also clamps.

  **Profile activation** Profile is usable only when
                         assessment_metadata-\>\>\'levels_completed\'
                         contains all 6 level IDs.

  **Unique version**     UNIQUE(user_id, version) --- enforced at DB
                         level, not just application layer.
  -----------------------------------------------------------------------

**1.6 Table: learning_parameters**

Stores all 32 derived learning parameters for a given profile. One row
per (profile_id, skill_id) combination --- skill-specific overrides are
baked in before storage. Immutable after creation.

  -------------------------------------------------------------------------------------------------------
  **Column**                             **Type**       **Constraints**         **Description**
  -------------------------------------- -------------- ----------------------- -------------------------
  id                                     UUID           PK DEFAULT              Primary key
                                                        uuid_generate_v4()      

  profile_id                             UUID           FK                      Source profile
                                                        cognitive_profiles.id   
                                                        NOT NULL                

  skill_id                               VARCHAR(64)    NOT NULL                Skill template reference
                                                                                slug --- \'drawing\',
                                                                                \'guitar\', etc.

  difficulty_slope                       NUMERIC(6,5)   NOT NULL CHECK BETWEEN  A: 0.6\*cog_cap +
                                                        0 AND 1                 0.4\*learn_tol

  phase_pacing                           NUMERIC(6,5)   NOT NULL CHECK BETWEEN  A: (attn_stab +
                                                        0 AND 1                 time_const) / 2

  entry_phase_offset                     NUMERIC(6,5)   NOT NULL CHECK BETWEEN  A: 0.5\*cog_cap +
                                                        0 AND 1                 0.5\*learn_tol

  repetition_intensity                   NUMERIC(6,5)   NOT NULL CHECK BETWEEN  A: 1 - learn_tol
                                                        0 AND 1                 

  session_duration                       NUMERIC(6,5)   NOT NULL CHECK BETWEEN  B: time_const \*
                                                        0 AND 1                 attn_stab

  micro_session_enabled                  SMALLINT       NOT NULL DEFAULT 0      B: 1 if attn_stab \< 0.4
                                                        CHECK IN (0,1)          

  fatigue_threshold                      NUMERIC(6,5)   NOT NULL CHECK BETWEEN  B: attn_stab \*
                                                        0 AND 1                 stress_res

  break_frequency                        NUMERIC(6,5)   NOT NULL CHECK BETWEEN  B: 1 - attn_stab
                                                        0 AND 1                 

  technique_density                      NUMERIC(6,5)   NOT NULL CHECK BETWEEN  C: cog_cap \* attn_stab
                                                        0 AND 1                 (clamped)

  concurrent_technique_limit             SMALLINT       NOT NULL CHECK BETWEEN  C:
                                                        0 AND 5                 floor(technique_density
                                                                                \* 5)

  abstraction_level                      NUMERIC(6,5)   NOT NULL CHECK BETWEEN  C: cognitive_capacity
                                                        0 AND 1                 

  instruction_granularity                NUMERIC(6,5)   NOT NULL CHECK BETWEEN  C: 1 - cognitive_capacity
                                                        0 AND 1                 

  checkpoint_frequency                   NUMERIC(6,5)   NOT NULL CHECK BETWEEN  D: 1 - attn_stab
                                                        0 AND 1                 

  checkpoint_rigidity                    NUMERIC(6,5)   NOT NULL CHECK BETWEEN  D: cog_cap \* stress_res
                                                        0 AND 1                 

  error_tolerance_threshold              NUMERIC(6,5)   NOT NULL CHECK BETWEEN  D: learning_tolerance
                                                        0 AND 1                 

  retry_limit                            SMALLINT       NOT NULL CHECK BETWEEN  D: round(learn_tol \* 5)
                                                        0 AND 5                 

  drill_depth                            NUMERIC(6,5)   NOT NULL CHECK BETWEEN  E: 1 - motor_baseline
                                                        0 AND 1                 

  variation_intensity                    NUMERIC(6,5)   NOT NULL CHECK BETWEEN  E: cog_cap \* stress_res
                                                        0 AND 1                 

  stress_exposure_rate                   NUMERIC(6,5)   NOT NULL CHECK BETWEEN  E: stress_res \* cog_cap
                                                        0 AND 1                 

  simulation_complexity                  NUMERIC(6,5)   NOT NULL CHECK BETWEEN  E: (cog_cap + motor_base)
                                                        0 AND 1                 / 2

  feedback_detail_level                  NUMERIC(6,5)   NOT NULL CHECK BETWEEN  F: 1 - cognitive_capacity
                                                        0 AND 1                 

  correction_delay_window                NUMERIC(6,5)   NOT NULL CHECK BETWEEN  F: stress_resilience
                                                        0 AND 1                 

  hint_activation_threshold              NUMERIC(6,5)   NOT NULL CHECK BETWEEN  F: 1 - learn_tol
                                                        0 AND 1                 

  precision_requirement                  NUMERIC(6,5)   NOT NULL CHECK BETWEEN  G: motor_baseline
                                                        0 AND 1                 

  speed_requirement                      NUMERIC(6,5)   NOT NULL CHECK BETWEEN  G: motor_base \* cog_cap
                                                        0 AND 1                 

  coordination_complexity                NUMERIC(6,5)   NOT NULL CHECK BETWEEN  G: motor_baseline
                                                        0 AND 1                 

  adaptation_sensitivity                 NUMERIC(6,5)   NOT NULL CHECK BETWEEN  H: 1 - stress_resilience
                                                        0 AND 1                 

  risk_zone_trigger_level                NUMERIC(6,5)   NOT NULL CHECK BETWEEN  H: 1 - ((learn_tol +
                                                        0 AND 1                 stress_res) / 2)

  regression_policy_strength             NUMERIC(6,5)   NOT NULL CHECK BETWEEN  H: 1 - learn_tol
                                                        0 AND 1                 

  phase_transition_sensitivity           NUMERIC(6,5)   NOT NULL CHECK BETWEEN  H: cog_cap \* stress_res
                                                        0 AND 1                 

  complexity_escalation_trigger          NUMERIC(6,5)   NOT NULL CHECK BETWEEN  H: cognitive_capacity
                                                        0 AND 1                 

  plateau_detection_threshold            NUMERIC(6,5)   NOT NULL CHECK BETWEEN  H: 1 - cog_cap
                                                        0 AND 1                 

  stability_requirement_before_advance   NUMERIC(6,5)   NOT NULL CHECK BETWEEN  H: attention_stability
                                                        0 AND 1                 

  created_at                             TIMESTAMPTZ    NOT NULL DEFAULT now()  Immutable creation
                                                                                timestamp
  -------------------------------------------------------------------------------------------------------

**Indexes**

  -------------------------------------------------------------------------
  **Index name**         **Column(s)**    **Purpose**
  ---------------------- ---------------- ---------------------------------
  lp_profile_skill_idx   (profile_id,     Unique --- one parameter set per
                         skill_id)        profile per skill. Primary lookup
                                          path.

  lp_profile_id_idx      profile_id       Fetch all skill parameters for a
                                          profile
  -------------------------------------------------------------------------

**1.7 Table: skill_templates**

Stores the static skill knowledge structures used by the roadmap
generator. One row per skill. Content is versioned --- a new version
creates a new row. The roadmap stores the version it was generated from.

  ----------------------------------------------------------------------------------------------
  **Column**         **Type**       **Constraints**      **Description**
  ------------------ -------------- -------------------- ---------------------------------------
  id                 UUID           PK DEFAULT           Primary key
                                    uuid_generate_v4()   

  skill_id           VARCHAR(64)    NOT NULL             Slug: \'drawing\', \'guitar\',
                                                         \'python-basics\'

  version            INT            NOT NULL DEFAULT 1   Template version --- new row per
                                                         structural change

  name               VARCHAR(128)   NOT NULL             Human-readable skill name

  domain             VARCHAR(64)    NOT NULL             Category: \'art\', \'music\',
                                                         \'programming\', \'language\'

  complexity_score   NUMERIC(4,3)   NOT NULL CHECK       Used in feasibility analysis LLM call
                                    BETWEEN 0 AND 1      

  structure          JSONB          NOT NULL             Full
                                                         phase/competency/technique/checkpoint
                                                         tree

  is_active          BOOLEAN        NOT NULL DEFAULT     False = retired version --- not
                                    true                 available to new users

  created_at         TIMESTAMPTZ    NOT NULL DEFAULT     Creation timestamp
                                    now()                
  ----------------------------------------------------------------------------------------------

**structure JSONB schema**

> { \"phases\": {
>
> \"fundamentals\": {
>
> \"competencies\": \[\"line control\", \"basic shapes\"\],
>
> \"techniques\": \[\"blind contour\", \"gesture drawing\"\],
>
> \"checkpoints\": \[\"produce 5 shapes within 5% proportion error\"\]
>
> }
>
> }
>
> }

**1.8 Table: roadmaps**

Stores the generated learning roadmap for a user-skill pair.
Deterministic --- same ProfileVector + SkillTemplate always produces
identical content. Immutable after creation. The fingerprint column
stores the SHA-256 hash of the serialized structure for integrity
verification.

  -------------------------------------------------------------------------------------
  **Column**         **Type**      **Constraints**          **Description**
  ------------------ ------------- ------------------------ ---------------------------
  id                 UUID          PK DEFAULT               Primary key
                                   uuid_generate_v4()       

  user_id            UUID          FK users.id NOT NULL     Roadmap owner

  skill_id           VARCHAR(64)   NOT NULL                 Skill template reference

  template_version   INT           NOT NULL                 Snapshot of
                                                            skill_template.version used

  profile_version    INT           NOT NULL                 Snapshot of
                                                            cognitive_profile.version
                                                            used

  parameters_id      UUID          FK                       Immutable snapshot of
                                   learning_parameters.id   params used
                                   NOT NULL                 

  structure          JSONB         NOT NULL                 Full roadmap: phases,
                                                            competencies, checkpoints,
                                                            durations, thresholds

  fingerprint        VARCHAR(64)   NOT NULL                 SHA-256 of canonical
                                                            serialized structure ---
                                                            integrity check

  status             VARCHAR(32)   NOT NULL DEFAULT         active \| completed \|
                                   \'active\'               abandoned

  created_at         TIMESTAMPTZ   NOT NULL DEFAULT now()   Generation timestamp

  completed_at       TIMESTAMPTZ   NULLABLE                 Set when status = completed
  -------------------------------------------------------------------------------------

**Indexes**

  ------------------------------------------------------------------------
  **Index name**        **Column(s)**    **Purpose**
  --------------------- ---------------- ---------------------------------
  rm_user_skill_idx     (user_id,        Fetch active roadmap for
                        skill_id,        user+skill --- expected to be
                        status)          unique per active status

  rm_fingerprint_idx    fingerprint      Integrity verification and
                                         deduplication check

  rm_status_idx         status           Filter active roadmaps for
                                         dashboard queries
  ------------------------------------------------------------------------

**1.9 Table: sessions**

One row per technique execution attempt. A session is the unit of work
--- it captures everything that happened during a single practice block.

  -------------------------------------------------------------------------------------
  **Column**                 **Type**       **Constraints**      **Description**
  -------------------------- -------------- -------------------- ----------------------
  id                         UUID           PK DEFAULT           Primary key
                                            uuid_generate_v4()   

  roadmap_id                 UUID           FK roadmaps.id NOT   Parent roadmap
                                            NULL                 

  user_id                    UUID           FK users.id NOT NULL Denormalized for query
                                                                 efficiency

  phase                      VARCHAR(64)    NOT NULL             Phase slug from
                                                                 roadmap structure

  technique_id               VARCHAR(64)    NOT NULL             Technique being
                                                                 executed

  attempt_number             INT            NOT NULL DEFAULT 1   Retry counter for this
                                                                 technique

  status                     VARCHAR(32)    NOT NULL DEFAULT     pending \| active \|
                                            \'pending\'          completed \| failed

  metrics_captured           JSONB          NOT NULL DEFAULT     Real-time signals:
                                            \'{}\'               accuracy, timing,
                                                                 error_count,
                                                                 step_completion

  protocol_steps_completed   JSONB          NOT NULL DEFAULT     Ordered list of
                                            \'\[\]\'             completed step IDs

  protocol_violations        JSONB          NOT NULL DEFAULT     Array of violation
                                            \'\[\]\'             records: { step_id,
                                                                 type, timestamp }

  failure_reason             VARCHAR(128)   NULLABLE             protocol_violation \|
                                                                 metric_threshold \|
                                                                 incomplete

  started_at                 TIMESTAMPTZ    NULLABLE             Set when status
                                                                 transitions to active

  ended_at                   TIMESTAMPTZ    NULLABLE             Set when status
                                                                 transitions to
                                                                 completed or failed

  created_at                 TIMESTAMPTZ    NOT NULL DEFAULT     Row creation timestamp
                                            now()                
  -------------------------------------------------------------------------------------

**Indexes**

  --------------------------------------------------------------------------
  **Index name**         **Column(s)**     **Purpose**
  ---------------------- ----------------- ---------------------------------
  sess_roadmap_idx       roadmap_id        Fetch all sessions for a roadmap

  sess_user_status_idx   (user_id, status) Dashboard: fetch active session
                                           for a user

  sess_technique_idx     (roadmap_id,      Count retries per technique
                         technique_id,     
                         attempt_number)   

  sess_started_at_idx    started_at        Time-range session analytics
  --------------------------------------------------------------------------

  -----------------------------------------------------------------------
  **Constraint**         **Definition**
  ---------------------- ------------------------------------------------
  **State machine**      status transitions enforced at application layer
                         only: pending → active → completed \| failed. No
                         trigger needed --- orchestration layer owns
                         transitions.

  **No skip**            A session in \'pending\' status cannot jump to
                         \'completed\'. Any attempt that bypasses
                         \'active\' is rejected by the orchestration
                         layer.

  **Failure = no         status=\'failed\' rows are terminal. A new
  progress**             session row is created for each retry attempt.
  -----------------------------------------------------------------------

**1.10 Table: evidence**

Stores all evidence submitted for checkpoint validation. One row per
evidence submission. Append-only --- never updated after validation.

  --------------------------------------------------------------------------------
  **Column**          **Type**      **Constraints**      **Description**
  ------------------- ------------- -------------------- -------------------------
  id                  UUID          PK DEFAULT           Primary key
                                    uuid_generate_v4()   

  session_id          UUID          FK sessions.id NOT   Parent session
                                    NULL                 

  user_id             UUID          FK users.id NOT NULL Denormalized for audit
                                                         queries

  checkpoint_id       VARCHAR(64)   NOT NULL             Checkpoint slug from
                                                         roadmap structure

  type                VARCHAR(32)   NOT NULL             numeric \| artifact \|
                                                         behavioral_log

  payload             JSONB         NOT NULL             Numeric values OR
                                                         artifact metadata

  artifact_url        TEXT          NULLABLE             Nhost presigned URL
                                                         (type=artifact only)

  artifact_key        TEXT          NULLABLE             Nhost object key for
                                                         server-side access

  mime_type           VARCHAR(64)   NULLABLE             image/png,
                                                         application/pdf,
                                                         video/mp4, etc.

  file_size_bytes     BIGINT        NULLABLE CHECK \<    Max 50MB enforced at DB
                                    52428800             level (52428800 bytes)

  validated           BOOLEAN       NOT NULL DEFAULT     Set to true after
                                    false                validation engine runs

  validation_result   JSONB         NULLABLE             { passed: bool,
                                                         threshold: float, actual:
                                                         float, reason: str }

  validated_at        TIMESTAMPTZ   NULLABLE             When validation ran

  created_at          TIMESTAMPTZ   NOT NULL DEFAULT     Upload timestamp
                                    now()                
  --------------------------------------------------------------------------------

**Indexes**

  ------------------------------------------------------------------------
  **Index name**        **Column(s)**    **Purpose**
  --------------------- ---------------- ---------------------------------
  ev_session_idx        session_id       Fetch all evidence for a session
                                         during validation

  ev_checkpoint_idx     (session_id,     Validate a specific checkpoint\'s
                        checkpoint_id)   evidence

  ev_validated_idx      validated        Filter unvalidated evidence in
                                         background job

  ev_user_idx           user_id          Audit log queries by user
  ------------------------------------------------------------------------

**payload JSONB schema by type**

numeric type:

> { \"accuracy_pct\": 0.91, \"time_taken_seconds\": 142,
> \"error_count\": 3 }

artifact type:

> { \"original_filename\": \"sketch_attempt3.png\", \"checksum_sha256\":
> \"abc123\...\" }

behavioral_log type:

> { \"steps_completed\": \[\"s1\",\"s2\",\"s3\"\], \"retry_count\": 1,
> \"total_duration_seconds\": 820 }

**1.11 Table: audit_log**

Append-only record of all sensitive business operations. No updates or
deletes ever issued against this table.

  ----------------------------------------------------------------------------
  **Column**      **Type**      **Constraints**      **Description**
  --------------- ------------- -------------------- -------------------------
  id              UUID          PK DEFAULT           Primary key
                                uuid_generate_v4()   

  user_id         UUID          FK users.id NULLABLE NULL for system-initiated
                                                     actions

  action          VARCHAR(64)   NOT NULL             Dot-separated:
                                                     \'profile.created\',
                                                     \'checkpoint.passed\',
                                                     \'auth.login_failed\'

  entity_type     VARCHAR(64)   NULLABLE             Table/domain name:
                                                     \'roadmap\', \'session\',
                                                     \'evidence\'

  entity_id       UUID          NULLABLE             PK of the affected row

  ip_address      INET          NULLABLE             Client IP --- NULL for
                                                     background jobs

  metadata        JSONB         NOT NULL DEFAULT     Action-specific context
                                \'{}\'               

  created_at      TIMESTAMPTZ   NOT NULL DEFAULT     Immutable event timestamp
                                now()                
  ----------------------------------------------------------------------------

**Audited actions**

-   auth.register, auth.login, auth.login_failed, auth.logout,
    auth.token_rotated

-   profile.created, profile.version_incremented

-   roadmap.generated, roadmap.completed, roadmap.abandoned

-   checkpoint.passed, checkpoint.failed

-   evidence.uploaded, evidence.validated

-   session.started, session.completed, session.failed

**1.12 Table: rag_chunks (pgvector)**

Stores text chunks and their embeddings for the RAG pipeline. The vector
column uses pgvector. Dimension must match the embedding model exactly.

  ------------------------------------------------------------------------------
  **Column**       **Type**        **Constraints**      **Description**
  ---------------- --------------- -------------------- ------------------------
  id               UUID            PK DEFAULT           Primary key
                                   uuid_generate_v4()   

  skill_id         VARCHAR(64)     NOT NULL             Skill this chunk belongs
                                                        to

  phase            VARCHAR(64)     NULLABLE             Phase slug --- NULL
                                                        means cross-phase
                                                        content

  technique_id     VARCHAR(64)     NULLABLE             Technique slug --- NULL
                                                        means phase-level
                                                        content

  doc_type         VARCHAR(32)     NOT NULL             tutorial \|
                                                        technique_guide \|
                                                        failure_analysis \|
                                                        resource

  source_url       TEXT            NULLABLE             Origin URL or file path

  chunk_index      INT             NOT NULL             Position within the
                                                        source document

  content          TEXT            NOT NULL             Raw text of the chunk
                                                        --- 512 tokens max

  embedding        vector(1536)    NOT NULL             OpenAI
                                                        text-embedding-3-small
                                                        output

  model_name       VARCHAR(64)     NOT NULL             Embedding model used ---
                                                        must match rag_config

  token_count      INT             NOT NULL             Actual token count of
                                                        content

  created_at       TIMESTAMPTZ     NOT NULL DEFAULT     Indexing timestamp
                                   now()                
  ------------------------------------------------------------------------------

**Vector indexes**

  ----------------------------------------------------------------------------
  **Index**                **Type**   **Configuration**    **Purpose**
  ------------------------ ---------- -------------------- -------------------
  rag_embedding_hnsw_idx   HNSW       vector_cosine_ops,   Fast approximate
                                      m=16,                nearest-neighbor
                                      ef_construction=64   search for
                                                           retrieval

  rag_skill_phase_idx      B-tree     (skill_id, phase,    Pre-filter by skill
                                      technique_id)        context before
                                                           vector search

  rag_doc_type_idx         B-tree     doc_type             Filter by content
                                                           type in query
                                                           construction
  ----------------------------------------------------------------------------

> *HNSW index parameters: m=16 (connections per layer) and
> ef_construction=64 are safe defaults for this dataset size. Increase
> ef_construction to 128 for better recall at the cost of index build
> time. Query-time ef_search should be set to at least 2x the top-k
> value (e.g. ef_search=14 for top-7 queries).*

**1.13 Table: rag_config**

Single-row configuration table recording the active embedding model.
Changing this invalidates the entire vector store and requires full
re-indexing.

  ---------------------------------------------------------------------------------
  **Column**         **Type**      **Constraints**     **Description**
  ------------------ ------------- ------------------- ----------------------------
  id                 INT           PK DEFAULT 1 CHECK  Singleton constraint ---
                                   (id = 1)            only one row allowed

  model_name         VARCHAR(64)   NOT NULL            \'text-embedding-3-small\'

  model_version      VARCHAR(32)   NOT NULL            Provider-specific version
                                                       identifier

  dimension          INT           NOT NULL            1536 for
                                                       text-embedding-3-small

  chunk_size         INT           NOT NULL DEFAULT    Max tokens per chunk
                                   512                 

  chunk_overlap      INT           NOT NULL DEFAULT 64 Token overlap between
                                                       adjacent chunks

  last_indexed_at    TIMESTAMPTZ   NULLABLE            When the full index was last
                                                       rebuilt

  updated_at         TIMESTAMPTZ   NOT NULL DEFAULT    Config last changed
                                   now()               
  ---------------------------------------------------------------------------------

**1.14 Migration Execution Order**

Run Alembic migrations in this exact sequence. Each migration is a
separate file with both upgrade() and downgrade() implemented.

  ------------------------------------------------------------------------------------
  **Order**   **Migration file**              **Creates**
  ----------- ------------------------------- ----------------------------------------
  001         create_extensions.py            uuid-ossp, vector, pg_trgm extensions

  002         create_users.py                 users table, updated_at trigger

  003         create_auth_tables.py           refresh_tokens, revoked_access_tokens

  004         create_cognitive_profiles.py    cognitive_profiles table + indexes

  005         create_learning_parameters.py   learning_parameters table + indexes

  006         create_skill_templates.py       skill_templates table

  007         create_roadmaps.py              roadmaps table + indexes

  008         create_sessions.py              sessions table + indexes

  009         create_evidence.py              evidence table + indexes

  010         create_audit_log.py             audit_log table

  011         create_rag_tables.py            rag_chunks (with vector column),
                                              rag_config, HNSW index
  ------------------------------------------------------------------------------------

**Part 2 --- Authentication System**

JWT-based stateless authentication using RS256 asymmetric signing.
Two-token architecture: short-lived access tokens in Authorization
headers, long-lived refresh tokens in httpOnly cookies. Full revocation,
rotation, and key rotation support.

**2.1 Files to Create**

  -------------------------------------------------------------------------------------
  **File path**                                 **Responsibility**
  --------------------------------------------- ---------------------------------------
  backend/auth/\_\_init\_\_.py                  Package init

  backend/auth/router.py                        FastAPI router --- mounts
                                                /auth/register, /auth/login,
                                                /auth/logout, /auth/refresh,
                                                /auth/logout-all

  backend/auth/service.py                       Business logic: register, login, token
                                                issuance, rotation, revocation

  backend/auth/schemas.py                       Pydantic request/response models

  backend/auth/dependencies.py                  FastAPI dependencies: get_current_user,
                                                require_auth

  backend/auth/jwt_handler.py                   Token creation, decode, validation, key
                                                loading

  backend/auth/password.py                      bcrypt hash + verify functions

  backend/auth/middleware.py                    Global auth middleware --- runs on
                                                every protected request

  backend/shared/db/models/user.py              SQLAlchemy ORM model for users table

  backend/shared/db/models/token.py             SQLAlchemy ORM models for
                                                refresh_tokens and
                                                revoked_access_tokens

  backend/shared/db/repositories/auth_repo.py   All DB queries for auth --- no raw SQL
                                                in service layer

  scripts/generate_keys.py                      One-time RS256 private/public key pair
                                                generation

  scripts/rotate_keys.py                        Key rotation --- adds new kid, marks
                                                old as transitioning

  .well-known/jwks.json                         Generated public key endpoint ---
                                                served at /.well-known/jwks.json

  tests/auth/test_register.py                   Registration flow unit + integration
                                                tests

  tests/auth/test_login.py                      Login, wrong password, suspended user
                                                tests

  tests/auth/test_tokens.py                     Access token validation, expiry,
                                                revocation tests

  tests/auth/test_refresh.py                    Refresh token rotation, reuse
                                                detection, expiry tests
  -------------------------------------------------------------------------------------

**2.2 RS256 Key Setup**

Run once per environment. Never commit private keys.

> \# generate_keys.py --- run once per environment
>
> from cryptography.hazmat.primitives.asymmetric import rsa
>
> from cryptography.hazmat.primitives import serialization
>
> import json, uuid, os
>
> private_key = rsa.generate_private_key(public_exponent=65537,
> key_size=2048)
>
> kid = str(uuid.uuid4()) \# key ID --- stored alongside the key
>
> \# Save private key to secrets manager or local .env.local (never
> committed)
>
> \# Save public key to .well-known/jwks.json (committed, public)

**Environment variables required**

  -----------------------------------------------------------------------
  **Variable**        **Value / Source**          **Where stored**
  ------------------- --------------------------- -----------------------
  JWT_PRIVATE_KEY     PEM-encoded RSA private key Secrets manager (Vault
                      (2048-bit)                  / AWS Secrets Manager).
                                                  Never .env

  JWT_PUBLIC_KEY      PEM-encoded RSA public key  .env.local for dev,
                                                  Secrets manager for
                                                  prod

  JWT_KID             UUID key ID matching the    Secrets manager
                      active JWKS entry           

  JWT_ACCESS_TTL      3600 (seconds)              Environment variable
                                                  --- .env.local or
                                                  secrets manager

  JWT_REFRESH_TTL     2592000 (30 days in         Environment variable
                      seconds)                    

  JWT_ALGORITHM       RS256                       Hardcoded in
                                                  jwt_handler.py --- not
                                                  configurable

  JWT_ISSUER          https://skillos.app (or     Environment variable
                      staging equivalent)         

  JWT_AUDIENCE        skillos-api                 Environment variable
  -----------------------------------------------------------------------

**2.3 Token Design**

**Access token claims**

  ---------------------------------------------------------------------------------
  **Claim**   **Type**   **Value**          **Purpose**
  ----------- ---------- ------------------ ---------------------------------------
  iss         string     JWT_ISSUER         Issuer --- validated on every decode

  aud         string     JWT_AUDIENCE       Audience --- validated on every decode

  sub         string     user.id (UUID)     Subject --- user identity

  jti         string     uuid4()            JWT ID --- enables individual
                                            revocation

  kid         string     JWT_KID            Key ID --- enables key rotation

  iat         integer    unix timestamp     Issued at

  exp         integer    iat +              Expiry --- 1 hour
                         JWT_ACCESS_TTL     

  email       string     user.email         Convenience claim --- avoids DB lookup
                                            for display

  status      string     user.status        Active status at issuance ---
                                            re-checked on sensitive ops
  ---------------------------------------------------------------------------------

**Refresh token design**

  -----------------------------------------------------------------------
  **Constraint**         **Definition**
  ---------------------- ------------------------------------------------
  **Format**             Opaque random token --- 64 bytes from
                         secrets.token_bytes(64), hex-encoded. NOT a JWT.

  **Storage**            SHA-256 hash stored in
                         refresh_tokens.token_hash. Raw token sent to
                         client once and never stored server-side.

  **Transport**          httpOnly cookie, SameSite=Strict, Secure=True.
                         Cookie name: skillos_refresh. Path=/auth.

  **Rotation**           Every use of a refresh token issues a new one
                         and immediately revokes the used one (revoked_at
                         = now()). Token reuse detection: if a revoked
                         token is presented, all tokens for that user are
                         invalidated.

  **Expiry**             30 days. After expiry, user must log in again
                         with credentials.

  **Binding**            Bound to user_id. Cannot be transferred between
                         accounts.
  -----------------------------------------------------------------------

**2.4 API Routes**

  -----------------------------------------------------------------------------------------------------
  **Method**   **Route**                **Auth**   **Request       **Response**    **Description**
                                                   body**                          
  ------------ ------------------------ ---------- --------------- --------------- --------------------
  POST         /auth/register           None       { email,        201 { user_id,  Validate email
                                                   password }      email }         format, check
                                                                                   uniqueness, hash
                                                                                   password, create
                                                                                   user, issue tokens

  POST         /auth/login              None       { email,        200 {           Verify password
                                                   password }      access_token    hash, check
                                                                   } + cookie      status=\'active\',
                                                                                   issue access +
                                                                                   refresh tokens,
                                                                                   write audit log

  POST         /auth/logout             Bearer     none            204             Revoke current
                                                                                   access token jti,
                                                                                   revoke current
                                                                                   refresh token, clear
                                                                                   cookie

  POST         /auth/logout-all         Bearer     none            204             Revoke all refresh
                                                                                   tokens for user,
                                                                                   revoke current
                                                                                   access token. Forces
                                                                                   re-login on all
                                                                                   devices.

  POST         /auth/refresh            Cookie     none            200 {           Validate refresh
                                                                   access_token    token hash, check
                                                                   } + new cookie  not revoked, issue
                                                                                   new access token,
                                                                                   rotate refresh token

  GET          /.well-known/jwks.json   None       none            200 JWKS object Public key endpoint
                                                                                   for external token
                                                                                   validation
  -----------------------------------------------------------------------------------------------------

**2.5 Auth Middleware & Dependencies**

Every protected route uses the get_current_user dependency. It performs
these checks in order --- fails fast on first violation:

-   Extract Bearer token from Authorization header. Return 401 if
    missing or malformed.

-   Decode JWT without verification to extract kid claim.

-   Load public key matching kid from JWKS. Return 401 if kid not found.

-   Verify JWT signature, iss, aud, exp. Return 401 on any failure.

-   Check jti against revoked_access_tokens table. Return 401 if found.

-   Load user from DB by sub claim. Return 401 if not found.

-   Check user.status == \'active\'. Return 403 if suspended.

-   Return User object to route handler.

> *Redis cache in front of the revoked_access_tokens check: cache key =
> \'revoked:{jti}\', TTL = remaining token lifetime. Cache hit =
> immediately return 401. Cache miss = DB query, if revoked then cache
> it. This prevents DB load from the revocation check on every request.*

**2.6 Rate Limiting on Auth Routes**

  ----------------------------------------------------------------------------
  **Route**          **Limit**       **Key**            **On breach**
  ------------------ --------------- ------------------ ----------------------
  /auth/register     5 / 10 min per  IP address         429 + Retry-After
                     IP                                 header

  /auth/login        10 / 10 min per IP address         429 + Retry-After +
                     IP                                 audit log
                                                        auth.login_failed

  /auth/refresh      30 / hour per   user_id from token 429 + Retry-After
                     user                               

  /auth/logout       20 / hour per   user_id            429
                     user                               

  /auth/logout-all   5 / hour per    user_id            429
                     user                               
  ----------------------------------------------------------------------------

**2.7 Key Rotation Procedure**

RS256 keys must be rotatable without invalidating existing tokens. The
JWKS endpoint supports multiple active keys simultaneously.

-   Generate new RS256 key pair with a new kid (UUID).

-   Add new public key to JWKS --- both old and new kid are now active
    in /.well-known/jwks.json.

-   Update JWT_PRIVATE_KEY and JWT_KID in secrets manager to point to
    new key.

-   Deploy application --- new tokens now use new kid. Old tokens (old
    kid) still validate against old public key in JWKS.

-   Wait for old access token TTL (1 hour) to expire --- all old access
    tokens have naturally expired.

-   Remove old kid from JWKS. Old key is retired.

-   Write audit log entry: system.key_rotated with old_kid and new_kid.

> *Never remove a key from JWKS before its issued tokens have expired.
> The window between adding the new key and removing the old key must be
> at least JWT_ACCESS_TTL (1 hour) plus any clock skew buffer (5 minutes
> recommended).*

**2.8 Required Test Cases**

  -------------------------------------------------------------------------
  **Test file**        **Test cases**
  -------------------- ----------------------------------------------------
  test_register.py     Valid registration, duplicate email (409), invalid
                       email format (400), weak password (400), missing
                       fields (422)

  test_login.py        Valid login, wrong password (401), nonexistent email
                       (401), suspended user (403), audit log written on
                       success and failure

  test_tokens.py       Valid access token accepted, expired token (401),
                       tampered signature (401), revoked jti (401), wrong
                       audience (401), wrong issuer (401)

  test_refresh.py      Valid rotation issues new token + revokes old, reuse
                       of revoked token invalidates all user tokens,
                       expired refresh token (401), missing cookie (401)

  test_logout.py       Logout revokes access token, logout-all revokes all
                       refresh tokens, subsequent requests with revoked
                       token return 401

  test_rate_limit.py   Login rate limit triggers after 10 attempts, 429
                       returned with Retry-After, register rate limit per
                       IP

  test_middleware.py   Protected route without token (401), protected route
                       with valid token (200), protected route after logout
                       (401)
  -------------------------------------------------------------------------

**2.9 Completion Checklist**

Phase A --- Build Step 1 (Database) is complete when:

-   All 11 Alembic migrations run cleanly on a fresh database

-   All downgrade() functions are implemented and tested

-   pgvector extension loads and HNSW index is queryable

-   All CHECK constraints reject out-of-range values

-   All UNIQUE constraints prevent duplicate rows

Phase A --- Build Step 3 (Auth System) is complete when:

-   All 7 test files pass with 0 failures

-   Rate limiting returns 429 with correct Retry-After on breach

-   Token reuse detection invalidates all user sessions

-   /.well-known/jwks.json serves the active public key

-   Key rotation procedure executed end-to-end in a staging environment

-   Audit log entries written for all audited auth actions

-   Revocation check covered by Redis cache in staging
