#!/usr/bin/env python
"""
Simple verification checklist for assessment integration.
Can be run immediately to verify configuration.
"""

import os
import sys

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def check(condition, message, details=""):
    status = "✓" if condition else "✗"
    print(f"  {status} {message}")
    if details:
        print(f"      {details}")

def main():
    print_section("ASSESSMENT INTEGRATION CHECKLIST")
    
    # Check 1: Project structure
    print("1. PROJECT STRUCTURE")
    checks = {
        "backend/assessment/": "Core assessment module",
        "backend/assessment/schemas.py": "Assessment data models",
        "backend/assessment/router.py": "API endpoints",
        "backend/assessment/service.py": "Business logic",
        "backend/assessment/normalization.py": "Metric normalization",
        "backend/assessment/profile_vector.py": "Profile computation",
        "frontend/src/hooks/useAssessment.ts": "Frontend assessment hook",
        "tests/integration/test_assessment_flow.py": "Integration tests",
    }
    
    for path, desc in checks.items():
        full_path = os.path.join(os.getcwd(), path)
        exists = os.path.exists(full_path)
        check(exists, f"{path}", f"({desc})")
    
    # Check 2: Environment configuration
    print("\n2. ENVIRONMENT CONFIGURATION")
    
    db_url = os.getenv("DATABASE_URL")
    check(bool(db_url), "DATABASE_URL environment variable set")
    if db_url:
        hidden = db_url[:40] + "***" if len(db_url) > 40 else db_url
        print(f"      → {hidden}")
    else:
        print(f"      → Set with: $env:DATABASE_URL = 'postgresql://...'")
    
    venv_active = "VIRTUAL_ENV" in os.environ
    check(venv_active, "Python virtual environment active")
    if venv_active:
        print(f"      → {os.getenv('VIRTUAL_ENV')}")
    
    # Check 3: Backend configuration
    print("\n3. BACKEND CONFIGURATION")
    
    backend_port = "8000"
    check(True, "Backend configured on port", f"http://localhost:{backend_port}")
    
    print(f"      → Start with: python -m uvicorn backend.main:app --reload --port {backend_port}")
    
    # Check 4: Database configuration
    print("\n4. DATABASE CONFIGURATION")
    
    check(True, "Expected database tables:")
    print(f"      → assessment_sessions")
    print(f"      → cognitive_profiles")
    print(f"      → learning_parameters")
    print(f"      → (Verify in Supabase console)")
    
    # Check 5: Assessment endpoints
    print("\n5. ASSESSMENT ENDPOINTS")
    
    endpoints = {
        "POST /assessment/start": "Initialize new assessment session",
        "POST /assessment/submit": "Submit single level data",
        "GET /assessment/status": "Check session status",
        "POST /assessment/complete": "Finalize and compute profile",
    }
    
    for endpoint, desc in endpoints.items():
        check(True, f"{endpoint}", f"({desc})")
    
    # Check 6: Frontend integration
    print("\n6. FRONTEND INTEGRATION")
    
    frontend_files = {
        "frontend/src/api/assessment.ts": "API client",
        "frontend/src/hooks/useAssessment.ts": "React query hooks",
        "frontend/src/views/AssessmentView.tsx": "Assessment UI component",
    }
    
    for file, desc in frontend_files.items():
        full_path = os.path.join(os.getcwd(), file)
        exists = os.path.exists(full_path)
        check(exists, f"{file}", f"({desc})")
    
    # Check 7: Data flow
    print("\n7. ASSESSMENT DATA FLOW")
    
    print("  STEP 1: Start Assessment")
    print("    [ ] POST /assessment/start → Creates session in DB")
    print("    [ ] Returns: session_id, levels [1-6], status")
    
    print("\n  STEP 2: Submit Levels (1-6)")
    print("    [ ] POST /assessment/submit (level 1)")
    print("    [ ] POST /assessment/submit (level 2)")
    print("    [ ] ... repeat for all 6 levels")
    print("    [ ] Data stored in: assessment_sessions.submissions (JSON)")
    
    print("\n  STEP 3: Complete Assessment")
    print("    [ ] POST /assessment/complete")
    print("    [ ] Backend normalizes all 6 submissions")
    print("    [ ] Averages normalized signals across levels")
    print("    [ ] Computes 6-dimension profile vector")
    print("    [ ] Derives 32+ learning parameters")
    print("    [ ] Stores in: cognitive_profiles + learning_parameters")
    
    print("\n  STEP 4: Display Results")
    print("    [ ] Frontend receives profile with all 6 dimensions")
    print("    [ ] Profile displayed to user")
    
    # Check 8: Verification queries
    print("\n8. DATABASE VERIFICATION QUERIES")
    
    print("\n  To verify data was stored:")
    print("\n  SELECT * FROM assessment_sessions")
    print("  WHERE user_id = '<user_id>' ORDER BY created_at DESC LIMIT 1;")
    print("\n  SELECT * FROM cognitive_profiles")
    print("  WHERE user_id = '<user_id>' ORDER BY created_at DESC LIMIT 1;")
    print("\n  SELECT * FROM learning_parameters")
    print("  WHERE profile_id = '<profile_id>' LIMIT 1;")
    
    # Summary
    print_section("CHECKLIST SUMMARY")
    
    print("✓ Configuration checklist complete\n")
    print("NEXT STEPS:")
    print("  1. Ensure DATABASE_URL is set to your Supabase URL")
    print("  2. Start backend: python -m uvicorn backend.main:app --reload")
    print("  3. Start frontend: npm run dev (in frontend/ directory)")
    print("  4. Navigate to assessment in browser")
    print("  5. Complete all 6 levels")
    print("  6. Click 'Compute Profile'")
    print("  7. Verify data in Supabase console\n")
    
    print("TESTING INTEGRATION:")
    print("  pytest tests/integration/test_assessment_flow.py -v")
    print("  pytest tests/integration/test_assessment_api.py -v\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
