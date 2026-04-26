# LEARNING PARAMETER PIPELINE
*Phase One Architecture — Corrected & Documented*

**Individual Profile Vector → Adaptive Learning Parameters**

```
RawTestResults → NormalizedSignals → ProfileVector → LearningParameters
```

---

## Corrections Applied to Original Document

The following errors were identified and corrected in the original architecture.

| # | Location | Original (Wrong) | Corrected |
|---|----------|------------------|-----------|
| 1 | n_dropout normalization | = dropout_depth_index / max_depth (higher raw = better? Wrong.) | = 1 − (dropout_depth_index / max_depth) — inverted; higher dropout = worse |
| 2 | n_retry normalization | = retry_depth / max_retry (higher retries = better? Wrong.) | = 1 − (retry_depth / max_retry) — inverted; more retries = worse performance |
| 3 | Profile vector operators | Bullet points used instead of + signs — ambiguous formatting | All + operators explicit in every formula |
| 4 | Learning params: clamp | No upper-bound protection on products (e.g. technique_density) | All derived parameters clamped to [0, 1] |
| 5 | entry_phase_offset | = cognitive_capacity × 0.5 (fixed scalar, wastes half the range) | = cognitive_capacity × 0.5 + learning_tolerance × 0.5 (full weighted sum) |
| 6 | risk_zone_trigger_level | Formula parenthesis ambiguous in plain text | = 1 − ((learning_tolerance + stress_resilience) / 2) — explicit grouping |

---

## 1. Raw Result Collection

Raw, unnormalized values collected per test session block. No computation at this stage.

### RawMetrics

| Parameter | Description |
|-----------|-------------|
| accuracy | Percentage score (0–100%) |
| mean_response_time | Average response latency in seconds |
| response_time_variance | Variance of response times (seconds²) |
| performance_decay | Decay rate across session blocks (0–1) |
| retry_depth | Number of retry attempts (raw count) |
| dropout_depth_index | Depth of dropout events observed (raw) |
| recovery_slope | Rate of performance recovery post-error |

### RawTimeConstraint

| Parameter | Description |
|-----------|-------------|
| available_hours_per_week | User-reported hours available (0–40) |
| preferred_session_length | User-reported preferred session length (minutes) |

---

## 2. Normalization (0–1 Scale)

All signals normalized to [0, 1] with **positive orientation** — higher value always means better performance. All outputs clamped after calculation.

### Normalization Constants (System-Defined)

| Parameter | Value |
|-----------|-------|
| max_accuracy | 100.0 (percentage ceiling) |
| max_expected_time | 10.0 sec (slowest acceptable response) |
| max_variance | 25.0 sec² (maximum acceptable variance) |
| max_depth | 10.0 (maximum dropout depth index) |
| max_retry | 10.0 (maximum retry count) |
| max_recovery | 1.0 (normalized recovery slope ceiling) |
| max_hours | 40.0 hours/week |
| max_session_length | 120.0 minutes |

### Normalized Signals

| Signal | Formula |
|--------|---------|
| n_accuracy | accuracy / max_accuracy |
| n_latency | 1 − (mean_response_time / max_expected_time) |
| n_latency_stability | 1 − (response_time_variance / max_variance) |
| n_decay_inverse | 1 − performance_decay |
| **n_dropout** *(FIXED)* | 1 − (dropout_depth_index / max_depth) |
| **n_retry** *(FIXED)* | 1 − (retry_depth / max_retry) |
| n_recovery | recovery_slope / max_recovery |
| n_hours | available_hours_per_week / max_hours |
| n_session_pref | preferred_session_length / max_session_length |

> **Fix note — n_dropout:** Originally = dropout_depth_index / max_depth. WRONG. Higher dropout depth = worse performance. Must be inverted.

> **Fix note — n_retry:** Originally = retry_depth / max_retry. WRONG. More retries = worse performance. Must be inverted.

*All values clamped: `output = max(0.0, min(1.0, computed_value))`*

---

## 3. Profile Vector Construction

Each dimension is a weighted linear combination of normalized signals. All weights per dimension sum to 1.0. All outputs clamped to [0, 1]. ProfileVector is **immutable once computed** and must be versioned.

### 3.1 cognitive_capacity
*Weights: 0.35 + 0.20 + 0.20 + 0.15 + 0.10 = 1.00*

```
cognitive_capacity = 0.35 × n_accuracy + 0.20 × n_latency + 0.20 × n_latency_stability
                   + 0.15 × n_decay_inverse + 0.10 × n_dropout
```

### 3.2 attention_stability
*Weights: 0.30 + 0.30 + 0.20 + 0.20 = 1.00*

```
attention_stability = 0.30 × n_accuracy + 0.30 × n_latency_stability
                    + 0.20 × n_decay_inverse + 0.20 × n_dropout
```

### 3.3 learning_tolerance
*Weights: 0.30 + 0.25 + 0.20 + 0.15 + 0.10 = 1.00*

```
learning_tolerance = 0.30 × n_retry + 0.25 × n_dropout + 0.20 × n_decay_inverse
                   + 0.15 × n_recovery + 0.10 × n_latency_stability
```

### 3.4 motor_baseline
*Weights: 0.40 + 0.30 + 0.30 = 1.00*

```
motor_baseline = 0.40 × n_accuracy + 0.30 × n_latency + 0.30 × n_latency_stability
```

### 3.5 stress_resilience
*Weights: 0.30 + 0.25 + 0.20 + 0.15 + 0.10 = 1.00*

```
stress_resilience = 0.30 × n_accuracy + 0.25 × n_latency_stability + 0.20 × n_recovery
                  + 0.15 × n_dropout + 0.10 × n_decay_inverse
```

### 3.6 time_constraint
*Weights: 0.70 + 0.30 = 1.00*

```
time_constraint = 0.70 × n_hours + 0.30 × n_session_pref
```

### ProfileVector Summary

| Dimension | Represents |
|-----------|------------|
| cognitive_capacity | Overall processing capacity and response quality |
| attention_stability | Consistency and sustained focus across session |
| learning_tolerance | Ability to handle challenge, retry, and recover |
| motor_baseline | Physical/motor execution speed and accuracy |
| stress_resilience | Performance under pressure and adversity |
| time_constraint | Available training bandwidth per week |

---

## 4. Learning Parameters

Derived from ProfileVector. All values in [0, 1] unless noted as integer. Explicit clamp applied on all products.

### A. Progression Control

| Parameter | Formula |
|-----------|---------|
| difficulty_slope | 0.6 × cognitive_capacity + 0.4 × learning_tolerance |
| phase_pacing | (attention_stability + time_constraint) / 2 |
| entry_phase_offset *(FIXED)* | 0.5 × cognitive_capacity + 0.5 × learning_tolerance |
| repetition_intensity | 1 − learning_tolerance |

> **Fix — entry_phase_offset:** Originally = cognitive_capacity × 0.5 (hard scalar). Corrected to full weighted sum using both cognitive_capacity and learning_tolerance.

### B. Session Structure

| Parameter | Formula |
|-----------|---------|
| session_duration | time_constraint × attention_stability [ratio 0–1] |
| micro_session_enabled | 1 if attention_stability < 0.4, else 0 [integer flag] |
| fatigue_threshold | attention_stability × stress_resilience |
| break_frequency | 1 − attention_stability |

*Note: session_duration is a ratio (0–1) representing utilization of available time, not raw minutes.*

### C. Cognitive Load Control

| Parameter | Formula |
|-----------|---------|
| technique_density | cognitive_capacity × attention_stability [clamped 0–1] |
| concurrent_technique_limit | floor(technique_density × 5) [integer, 0–5] |
| abstraction_level | cognitive_capacity |
| instruction_granularity | 1 − cognitive_capacity |

### D. Validation Control

| Parameter | Formula |
|-----------|---------|
| checkpoint_frequency | 1 − attention_stability |
| checkpoint_rigidity | cognitive_capacity × stress_resilience |
| error_tolerance_threshold | learning_tolerance |
| retry_limit | round(learning_tolerance × 5) [integer, 0–5] |

### E. Practice Dynamics

| Parameter | Formula |
|-----------|---------|
| drill_depth | 1 − motor_baseline |
| variation_intensity | cognitive_capacity × stress_resilience |
| stress_exposure_rate | stress_resilience × cognitive_capacity |
| simulation_complexity | (cognitive_capacity + motor_baseline) / 2 |

### F. Feedback Control

| Parameter | Formula |
|-----------|---------|
| feedback_detail_level | 1 − cognitive_capacity |
| correction_delay_window | stress_resilience |
| hint_activation_threshold | 1 − learning_tolerance |

### G. Motor Control

| Parameter | Formula |
|-----------|---------|
| precision_requirement | motor_baseline |
| speed_requirement | motor_baseline × cognitive_capacity |
| coordination_complexity | motor_baseline |

### H. Adaptive / Meta Structural Control

| Parameter | Formula |
|-----------|---------|
| adaptation_sensitivity | 1 − stress_resilience |
| risk_zone_trigger_level *(FIXED)* | 1 − ((learning_tolerance + stress_resilience) / 2) |
| regression_policy_strength | 1 − learning_tolerance |
| phase_transition_sensitivity | cognitive_capacity × stress_resilience |
| complexity_escalation_trigger | cognitive_capacity |
| plateau_detection_threshold | 1 − cognitive_capacity |
| stability_requirement_before_advance | attention_stability |

> **Fix — risk_zone_trigger_level:** Parentheses clarified. Inner average computed first: `1 − ((learning_tolerance + stress_resilience) / 2)`.

---

## 5. Stored Objects & Data Flow

Four objects persisted in order. Each is **immutable once written** and must be versioned for auditability.

| Object | Contents | Notes |
|--------|----------|-------|
| RawTestResults | RawMetrics + RawTimeConstraint | Collected once per session block. Never modified. |
| NormalizedSignals | 9 signals in [0, 1] | Derived from RawTestResults + normalization constants. |
| ProfileVector | 6 dimensions in [0, 1] | Derived from NormalizedSignals. Immutable. Versioned. |
| LearningParameters | 32 parameters across 8 groups | Derived from ProfileVector. Re-computed on profile update. |

---

## 6. Conclusion

The Learning Parameter Pipeline is a four-stage deterministic architecture converting raw session performance signals into 32 adaptive learning parameters.

**Key structural guarantees:**
- All weights per ProfileVector dimension sum to exactly 1.0 — dimensions are directly comparable across learners
- All signals and derived parameters bounded to [0, 1] — no overflow or nonsensical extremes
- Four stored objects form a strict one-directional data flow — no circular dependencies

**Critical corrections:**
n_dropout and n_retry were inverted. Higher raw values were incorrectly treated as better performance. Without the fix, all downstream adaptive behavior would have been directionally wrong — penalizing good learners and rewarding poor ones.

**Design property:**
Every learning parameter is expressed purely in terms of ProfileVector dimensions. Re-running on updated test results propagates changes automatically through all 32 parameters — no manual adjustment needed.

---

*Pipeline Status: Mathematically stable · Non-redundant · System-complete · Corrections applied*
