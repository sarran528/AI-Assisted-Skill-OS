# CORS & Authentication Troubleshooting Guide

## Problem Summary

**Error**: `Access to XMLHttpRequest at 'http://localhost:8000/api/v1/assessment/status' from origin 'http://localhost:3000' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`

**Root Causes**:
1. **Middleware Order**: Auth middleware runs before CORS middleware can respond with proper headers
2. **Missing Authorization Header**: Frontend not sending JWT Bearer token
3. **Backend Not Running**: Server may not be accessible on port 8000
4. **Frontend URL Mismatch**: Frontend might be on port 3000 instead of 5173 (Vite default)

---

## Solution: Fix Backend Middleware Order

### Issue: Middleware Order in `backend/main.py`

The authentication middleware runs BEFORE the CORS middleware, so when requests lack auth tokens, the 401 error is returned without CORS headers.

**Fix**: Reorder middleware so CORS middleware applies first

```python
# backend/main.py - Lines 27-41

def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="SkillOS", version="0.1.0")
    app.state.limiter = limiter
    
    # ADD CORS MIDDLEWARE FIRST - This must be applied before other middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins.split(","),
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
        allow_credentials=True,
    )
    
    # THEN add other middleware
    app.add_middleware(SlowAPIMiddleware)
    app.middleware("http")(request_id_middleware)
    app.middleware("http")(auth_context_middleware)

    # ... rest of the code
```

---

## Quick Start: Local Development Setup

### Step 1: Verify Backend Configuration

Check your `.env.local` file includes:

```bash
# .env.local
APP_ENV=local
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Database (use Supabase or local PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:[password]@localhost:5432/skillos

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Keys (generate if missing)
JWT_PRIVATE_KEY=your-private-key-here
JWT_PUBLIC_KEY=your-public-key-here
JWT_KID=local-1
```

### Step 2: Start Backend (Terminal 1)

```powershell
# Activate venv
.\.venv-1\Scripts\Activate.ps1

# Start backend on port 8000
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process
```

### Step 3: Start Frontend (Terminal 2)

```powershell
cd frontend

# Install dependencies
npm install

# Start dev server (default port 5173)
npm run dev
```

**Expected Output**:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  press h to show help
```

### Step 4: Verify Backend Health (Terminal 3)

```powershell
# Check backend health
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","database":"connected","redis":"connected"}
```

---

## Frontend: Configure Correct Backend URL

### Issue: Frontend pointing to wrong backend URL

**Check**: `frontend/.env` or `frontend/.env.local`

```bash
# frontend/.env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_API_V1_BASE_URL=http://localhost:8000/api/v1
```

**Check frontend API service configuration**: `frontend/src/services/api.ts` or similar

```typescript
// Example: frontend/src/services/api.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_V1_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Important for CORS with credentials
});

// Add request interceptor to include auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token'); // Or from your auth store
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
```

---

## Frontend: Send Authorization Header

### Problem: No Bearer Token Sent

The `/assessment/status` endpoint requires authentication. The frontend must:

1. **Store JWT token after login**
2. **Send token in every request header**

### Example: React Hook for Assessment Status

```typescript
// frontend/src/hooks/useAssessmentStatus.ts
import { useEffect, useState } from 'react';
import axios from 'axios';

export function useAssessmentStatus() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      
      // Get token from localStorage or auth store
      const token = localStorage.getItem('auth_token');
      
      if (!token) {
        setError('No authentication token found');
        setLoading(false);
        return;
      }

      const response = await axios.get(
        'http://localhost:8000/api/v1/assessment/status',
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          withCredentials: true, // Include credentials for CORS
        }
      );

      setStatus(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch assessment status:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return { status, loading, error, refetch: fetchStatus };
}
```

### Usage in Component

```typescript
// frontend/src/pages/Assessment.tsx
import { useAssessmentStatus } from '@/hooks/useAssessmentStatus';

export function AssessmentPage() {
  const { status, loading, error } = useAssessmentStatus();

  if (loading) return <div>Loading assessment status...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Assessment Status</h1>
      <pre>{JSON.stringify(status, null, 2)}</pre>
    </div>
  );
}
```

---

## Testing CORS Directly

### Test 1: Health Check (No Auth Required)

```powershell
# This should work without auth
curl http://localhost:8000/health

# Expected: 200 OK
# {"status":"ok","database":"connected","redis":"connected"}
```

### Test 2: Assessment Status (Requires Auth)

```powershell
# First, get a token by logging in
$loginResponse = curl -X POST `
  -H "Content-Type: application/json" `
  -d '{"email":"user@example.com","password":"password"}' `
  http://localhost:8000/api/v1/auth/login | ConvertFrom-Json

$token = $loginResponse.access_token

# Then call the status endpoint with the token
curl -H "Authorization: Bearer $token" `
  http://localhost:8000/api/v1/assessment/status

# Expected: 200 OK with assessment status
```

### Test 3: CORS Preflight (OPTIONS Request)

```powershell
curl -X OPTIONS `
  -H "Origin: http://localhost:3000" `
  -H "Access-Control-Request-Method: GET" `
  -H "Access-Control-Request-Headers: Authorization" `
  http://localhost:8000/api/v1/assessment/status

# Expected headers in response:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
# Access-Control-Allow-Headers: Authorization, Content-Type, X-Requested-With
# Access-Control-Allow-Credentials: true
```

---

## Debugging Checklist

- [ ] **Backend Running?**
  ```powershell
  # Should return 200
  curl http://localhost:8000/health
  ```

- [ ] **Database Connected?**
  ```powershell
  # Check response includes "database": "connected"
  curl http://localhost:8000/health | ConvertFrom-Json | Select-Object database
  ```

- [ ] **CORS Configuration in .env**
  ```powershell
  # Check .env.local includes frontend URL
  type .env.local | grep CORS_ALLOWED_ORIGINS
  ```

- [ ] **Frontend Token Stored?**
  ```javascript
  // In browser console (F12 -> Console)
  localStorage.getItem('auth_token')
  // Should return JWT token, not null
  ```

- [ ] **Authorization Header Sent?**
  ```javascript
  // In browser console Network tab, check the request header:
  // Authorization: Bearer eyJhbGc...
  ```

- [ ] **Correct Endpoint Called?**
  ```javascript
  // Browser console Network tab - check URL:
  // http://localhost:8000/api/v1/assessment/status
  ```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `No 'Access-Control-Allow-Origin' header` | Backend not running or middleware order wrong | Run backend, reorder middleware per fix above |
| `401 Unauthorized` | No auth token or invalid token | Store token after login, send in Authorization header |
| `CORS policy: No 'Access-Control-Allow-Credentials'` | Missing `allow_credentials=True` | Add `allow_credentials=True` to CORSMiddleware |
| `net::ERR_FAILED 500` | Backend error, likely auth validation | Check backend logs, ensure token is valid |
| `404 Not Found` | Wrong endpoint path | Verify endpoint URL matches backend router |
| `Connection refused on localhost:8000` | Backend not running | Start backend with uvicorn command |

---

## Environment Variables Reference

### Backend (.env.local)

```bash
APP_ENV=local
API_BASE_URL=http://localhost:8000
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/skillos
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# CORS Configuration - includes all frontend URLs
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173

# JWT
JWT_PRIVATE_KEY=your-private-key
JWT_PUBLIC_KEY=your-public-key
JWT_KID=local-1

# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Frontend (.env.local)

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_API_V1_BASE_URL=http://localhost:8000/api/v1
```

---

## Production CORS Configuration

For production deployments, update `.env` or Docker environment:

```bash
# Restrict to specific domains only
CORS_ALLOWED_ORIGINS=https://skillos.com,https://www.skillos.com,https://app.skillos.com

# Never use * in production - it disables credentials
# ❌ CORS_ALLOWED_ORIGINS=*

# Use environment-specific config
# DEV: localhost:3000,localhost:5173
# STAGING: https://staging.skillos.com
# PROD: https://skillos.com
```

---

## Next Steps

1. ✅ Apply middleware fix to `backend/main.py`
2. ✅ Verify `.env.local` has correct CORS origins
3. ✅ Restart backend: `python -m uvicorn backend.main:app --reload`
4. ✅ Check browser Network tab for Authorization header
5. ✅ Run health check: `curl http://localhost:8000/health`
6. ✅ Test API endpoint with auth token

Once fixed, the assessment status endpoint should respond with 200 OK and proper CORS headers.

