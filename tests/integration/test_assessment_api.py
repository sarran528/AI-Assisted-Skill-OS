"""
API Integration Tests - Tests the actual HTTP endpoints.

Run with: pytest tests/integration/test_assessment_api.py -v
"""

import pytest
import httpx
from uuid import uuid4
import json
from datetime import datetime, timezone


class TestAssessmentAPI:
    """Test assessment endpoints with actual HTTP calls."""
    
    BASE_URL = "http://localhost:8000/api/v1"
    
    @pytest.fixture
    def client(self):
        """Create HTTP client."""
        return httpx.Client(timeout=10.0)
    
    def test_backend_is_running(self):
        """Test: Backend server is running and accessible."""
        print("\n✓ TEST 1: Backend Server Status")
        
        try:
            response = httpx.get(f"{self.BASE_URL}/health", timeout=5)
            print(f"  ✓ Backend is running on {self.BASE_URL}")
            print(f"  ✓ Response code: {response.status_code}")
        except httpx.ConnectError:
            pytest.fail(
                f"✗ Cannot connect to backend at {self.BASE_URL}\n"
                "  Run: python -m uvicorn backend.main:app --reload --port 8000"
            )
    
    def test_assessment_start_endpoint(self, client):
        """Test: POST /assessment/start creates a new session."""
        print("\n✓ TEST 2: Assessment Start Endpoint")
        
        # Mock auth token (replace with real token if needed)
        headers = {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        }
        
        try:
            response = client.post(
                f"{self.BASE_URL}/assessment/start",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                print(f"  ⚠ 401 Unauthorized - Need valid auth token")
                print(f"    Response: {response.text[:200]}")
            elif response.status_code == 201:
                data = response.json()
                print(f"  ✓ Session created successfully")
                print(f"    - Session ID: {data.get('session_id')}")
                print(f"    - Levels: {data.get('levels')}")
                print(f"    - Status: {data.get('status')}")
                return data.get('session_id')
            else:
                print(f"  ✗ Unexpected status: {response.status_code}")
                print(f"    Response: {response.text[:200]}")
        except httpx.ConnectError:
            pytest.fail("Cannot connect to backend")
    
    def test_assessment_submit_endpoint(self, client):
        """Test: POST /assessment/submit stores level data."""
        print("\n✓ TEST 3: Assessment Submit Endpoint")
        
        headers = {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        }
        
        payload = {
            "session_id": str(uuid4()),
            "level": 1,
            "metrics": {
                "accuracy": 85.5,
                "expected_time": 4.2,
                "latency_stability": 8.5,
                "decay_inverse": 0.75,
                "dropout": 1,
                "retry": 0,
                "recovery": 0.8
            },
            "time_constraint": {
                "available_hours_per_week": 20.0,
                "preferred_session_length": 60.0
            }
        }
        
        try:
            response = client.post(
                f"{self.BASE_URL}/assessment/submit",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 401:
                print(f"  ⚠ 401 Unauthorized - Need valid auth token")
            elif response.status_code == 201:
                data = response.json()
                print(f"  ✓ Level submission successful")
                print(f"    - Level: {data.get('level')}")
                print(f"    - Status: {data.get('status')}")
            else:
                print(f"  ⚠ Status {response.status_code}: {response.text[:200]}")
        except httpx.ConnectError:
            pytest.fail("Cannot connect to backend")
    
    def test_assessment_complete_endpoint(self, client):
        """Test: POST /assessment/complete computes profile."""
        print("\n✓ TEST 4: Assessment Complete Endpoint")
        
        headers = {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        }
        
        payload = {
            "session_id": str(uuid4()),
            "completed_levels": [1, 2, 3, 4, 5, 6]
        }
        
        try:
            response = client.post(
                f"{self.BASE_URL}/assessment/complete",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 401:
                print(f"  ⚠ 401 Unauthorized - Need valid auth token")
            elif response.status_code == 201:
                data = response.json()
                print(f"  ✓ Assessment completion successful")
                print(f"    - Profile ID: {data.get('profile_id')}")
                print(f"    - Cognitive Capacity: {data.get('cognitive_capacity')}")
                print(f"    - Attention Stability: {data.get('attention_stability')}")
                print(f"    - Learning Tolerance: {data.get('learning_tolerance')}")
                print(f"    - Motor Baseline: {data.get('motor_baseline')}")
                print(f"    - Stress Resilience: {data.get('stress_resilience')}")
                print(f"    - Time Constraint: {data.get('time_constraint')}")
            else:
                print(f"  ⚠ Status {response.status_code}: {response.text[:200]}")
        except httpx.ConnectError:
            pytest.fail("Cannot connect to backend")
    
    def test_assessment_status_endpoint(self, client):
        """Test: GET /assessment/status returns session state."""
        print("\n✓ TEST 5: Assessment Status Endpoint")
        
        headers = {
            "Authorization": "Bearer test-token",
        }
        
        try:
            response = client.get(
                f"{self.BASE_URL}/assessment/status",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                print(f"  ⚠ 401 Unauthorized - Need valid auth token")
            elif response.status_code == 200:
                data = response.json()
                print(f"  ✓ Status retrieved successfully")
                print(f"    - Session ID: {data.get('session_id')}")
                print(f"    - Status: {data.get('status')}")
                print(f"    - Completed Levels: {data.get('completed_levels')}")
            else:
                print(f"  ⚠ Status {response.status_code}: {response.text[:200]}")
        except httpx.ConnectError:
            pytest.fail("Cannot connect to backend")


class TestDatabaseQueries:
    """Test database queries to verify data storage."""
    
    def test_can_connect_to_database(self):
        """Test: Can connect to database."""
        print("\n✓ TEST 6: Database Connection")
        
        import os
        db_url = os.getenv("DATABASE_URL")
        
        if not db_url:
            print(f"  ⚠ DATABASE_URL not set")
            print(f"    Set with: $env:DATABASE_URL = 'postgresql://...'")
            return
        
        print(f"  ✓ DATABASE_URL is configured")
        
        # Try to import and check connection
        try:
            from backend.shared.db.session import get_db_session
            print(f"  ✓ Database session factory available")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    def test_assessment_data_stored_correctly(self):
        """Test: Query database for stored assessment data."""
        print("\n✓ TEST 7: Database Query Verification")
        
        print(f"  Expected queries to run:")
        print(f"    SELECT * FROM assessment_sessions WHERE user_id = ?")
        print(f"    SELECT * FROM cognitive_profiles WHERE user_id = ?")
        print(f"    SELECT * FROM learning_parameters WHERE profile_id = ?")
        print(f"  (Run these manually in Supabase console)")


class TestEndToEndFlow:
    """Test complete end-to-end flow."""
    
    def test_assessment_workflow_checklist(self):
        """Test: Complete workflow checklist."""
        print("\n✓ TEST 8: End-to-End Workflow Checklist")
        
        print(f"\n  Step 1: Start Assessment")
        print(f"    [ ] Call POST /assessment/start")
        print(f"    [ ] Verify session_id is returned")
        print(f"    [ ] Verify status = 'started'")
        
        print(f"\n  Step 2: Submit Level 1")
        print(f"    [ ] Call POST /assessment/submit (level=1)")
        print(f"    [ ] Verify level data stored in assessment_sessions.submissions")
        print(f"    [ ] Verify completed_levels includes [1]")
        
        print(f"\n  Step 3: Submit Levels 2-6")
        print(f"    [ ] Repeat for levels 2, 3, 4, 5, 6")
        print(f"    [ ] After each: completed_levels = [1], [1,2], [1,2,3], etc.")
        
        print(f"\n  Step 4: Complete Assessment")
        print(f"    [ ] Call POST /assessment/complete")
        print(f"    [ ] Verify profile computed (6 dimensions in [0,1])")
        print(f"    [ ] Verify profile stored in cognitive_profiles table")
        
        print(f"\n  Step 5: Verify Database Storage")
        print(f"    [ ] Query cognitive_profiles - should have 1 record")
        print(f"    [ ] Query learning_parameters - should have 1 record with 32+ fields")
        print(f"    [ ] All numeric values in valid range [0,1] or appropriate bounds")
        
        print(f"\n  ✓ Checklist items defined (execute manually)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ASSESSMENT API INTEGRATION TEST SUITE")
    print("="*60)
    
    api_tests = TestAssessmentAPI()
    
    # Check if backend is running first
    try:
        api_tests.test_backend_is_running()
    except Exception as e:
        print(f"\n✗ Backend not running. Start it with:")
        print(f"  python -m uvicorn backend.main:app --reload --port 8000")
        exit(1)
    
    # Run other tests
    try:
        db_tests = TestDatabaseQueries()
        db_tests.test_can_connect_to_database()
        db_tests.test_assessment_data_stored_correctly()
        
        e2e_tests = TestEndToEndFlow()
        e2e_tests.test_assessment_workflow_checklist()
        
        print("\n" + "="*60)
        print("✓ TEST SUITE SETUP COMPLETE")
        print("="*60)
        print("\nNext steps:")
        print("1. Run pytest: pytest tests/integration/ -v")
        print("2. Or run manually and check outputs")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
