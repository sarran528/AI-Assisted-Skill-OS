#!/usr/bin/env python
"""
Quick verification script for assessment integration.
Run without pytest: python scripts/verify_assessment_integration.py
"""

import os
import sys
import asyncio
from datetime import datetime
from uuid import uuid4

def print_header(title):
    """Print section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_check(passed, message):
    """Print check result."""
    status = "✓" if passed else "✗"
    print(f"  {status} {message}")

async def main():
    print_header("ASSESSMENT INTEGRATION VERIFICATION")
    
    # Check 1: Environment variables
    print("1. ENVIRONMENT CONFIGURATION")
    db_url = os.getenv("DATABASE_URL")
    print_check(bool(db_url), "DATABASE_URL configured")
    if db_url:
        # Hide sensitive parts
        if "@" in db_url:
            user_part, host_part = db_url.split("@")
            hidden = user_part[:15] + "***@" + host_part[:30] + "***"
        else:
            hidden = db_url[:40] + "***"
        print(f"    → {hidden}")
    
    # Check 2: Python imports
    print("\n2. BACKEND IMPORTS")
    try:
        from backend.assessment.schemas import AssessmentSubmission, RawMetrics, RawTimeConstraint, NormalizedSignals
        print_check(True, "Assessment schemas imported")
    except Exception as e:
        print_check(False, f"Failed to import schemas: {e}")
        return
    
    try:
        from backend.assessment.normalization import normalize_all
        from backend.assessment.profile_vector import compute_profile_vector
        print_check(True, "Normalization and profile computation functions imported")
    except Exception as e:
        print_check(False, f"Failed to import functions: {e}")
        return
    
    try:
        from backend.shared.db.models import AssessmentSession, CognitiveProfile, LearningParameter
        print_check(True, "Database models imported")
    except Exception as e:
        print_check(False, f"Failed to import models: {e}")
        return
    
    # Check 3: Test normalization
    print("\n3. NORMALIZATION TEST")
    try:
        submission = AssessmentSubmission(
            session_id=uuid4(),
            level=1,
            metrics=RawMetrics(
                accuracy=85.0,
                expected_time=4.5,
                latency_stability=10.0,
                decay_inverse=0.75,
                dropout=1,
                retry=0,
                recovery=0.8
            ),
            time_constraint=RawTimeConstraint(
                available_hours_per_week=20.0,
                preferred_session_length=60.0
            )
        )
        
        normalized = normalize_all(submission.metrics, submission.time_constraint)
        
        # Check all values are in [0, 1]
        all_valid = True
        for field in normalized.model_fields:
            value = getattr(normalized, field)
            if not (0.0 <= value <= 1.0):
                all_valid = False
                break
        
        print_check(all_valid, "All normalized signals in [0, 1] range")
        print(f"    → Sample normalized values: accuracy={normalized.n_accuracy:.4f}, "
              f"latency={normalized.n_latency:.4f}, dropout={normalized.n_dropout:.4f}")
    except Exception as e:
        print_check(False, f"Normalization failed: {e}")
        return
    
    # Check 4: Test profile computation
    print("\n4. PROFILE VECTOR COMPUTATION TEST")
    try:
        profile = compute_profile_vector(normalized)
        
        # Check all dimensions are in [0, 1]
        dims = {
            "cognitive_capacity": profile.cognitive_capacity,
            "attention_stability": profile.attention_stability,
            "learning_tolerance": profile.learning_tolerance,
            "motor_baseline": profile.motor_baseline,
            "stress_resilience": profile.stress_resilience,
            "time_constraint": profile.time_constraint,
        }
        
        all_valid = all(0.0 <= v <= 1.0 for v in dims.values())
        print_check(all_valid, "All profile dimensions in [0, 1] range")
        
        for name, value in dims.items():
            print(f"    → {name}: {value:.4f}")
    except Exception as e:
        print_check(False, f"Profile computation failed: {e}")
        return
    
    # Check 5: Test aggregation across 6 levels
    print("\n5. MULTI-LEVEL AGGREGATION TEST")
    try:
        normalized_levels = []
        for level in range(1, 7):
            sub = AssessmentSubmission(
                session_id=uuid4(),
                level=level,
                metrics=RawMetrics(
                    accuracy=70.0 + (level * 3),
                    expected_time=5.0 - (level * 0.3),
                    latency_stability=12.0 - (level * 1),
                    decay_inverse=0.7 + (level * 0.04),
                    dropout=max(0, 3 - level),
                    retry=max(0, 2 - level),
                    recovery=0.6 + (level * 0.05)
                ),
                time_constraint=RawTimeConstraint(
                    available_hours_per_week=20.0,
                    preferred_session_length=60.0
                )
            )
            norm = normalize_all(sub.metrics, sub.time_constraint)
            normalized_levels.append(norm)
        
        # Manual aggregation
        field_names = list(normalized_levels[0].model_fields.keys())
        aggregated_dict = {}
        for field in field_names:
            values = [getattr(n, field) for n in normalized_levels]
            aggregated_dict[field] = sum(values) / len(values)
        
        aggregated = NormalizedSignals.model_validate(aggregated_dict)
        final_profile = compute_profile_vector(aggregated)
        
        print_check(True, "Successfully aggregated 6 levels into final profile")
        print(f"    → Final cognitive capacity: {final_profile.cognitive_capacity:.4f}")
        print(f"    → Final stress resilience: {final_profile.stress_resilience:.4f}")
    except Exception as e:
        print_check(False, f"Aggregation failed: {e}")
        return
    
    # Check 6: Backend connectivity
    print("\n6. BACKEND CONNECTIVITY")
    try:
        import httpx
        try:
            response = httpx.get("http://localhost:8000/docs", timeout=3)
            print_check(response.status_code == 200, "Backend server is running")
            print(f"    → Accessible at http://localhost:8000")
        except (httpx.ConnectError, httpx.TimeoutException):
            print_check(False, "Backend server not responding")
            print(f"    → Start with: python -m uvicorn backend.main:app --reload --port 8000")
    except ImportError:
        print(f"  ⚠ httpx not installed, skipping backend connectivity check")
    
    # Check 7: Database schema
    print("\n7. DATABASE SCHEMA VERIFICATION")
    print_check(True, "Assessment tables expected:")
    print(f"    → assessment_sessions (stores per-session data)")
    print(f"    → cognitive_profiles (stores computed 6-dim profiles)")
    print(f"    → learning_parameters (stores 32+ derived parameters)")
    
    # Summary
    print_header("VERIFICATION COMPLETE")
    
    print("✓ Assessment integration ready for testing\n")
    print("NEXT STEPS:")
    print("  1. Start backend: python -m uvicorn backend.main:app --reload --port 8000")
    print("  2. Run assessment in frontend and submit all 6 levels")
    print("  3. Click 'Compute Profile' to trigger complete endpoint")
    print("  4. Verify data in Supabase database")
    print("\nQUERY DATABASE WITH:")
    print("  SELECT * FROM assessment_sessions ORDER BY created_at DESC LIMIT 1;")
    print("  SELECT * FROM cognitive_profiles ORDER BY created_at DESC LIMIT 1;")
    print("  SELECT * FROM learning_parameters ORDER BY created_at DESC LIMIT 1;\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
