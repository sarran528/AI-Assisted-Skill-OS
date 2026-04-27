# CORS Error Quick Fix

## TL;DR - The Fix (30 seconds)

**Error**: `Access to XMLHttpRequest ... has been blocked by CORS policy`

**Fix**: Restart backend after these changes:

### 1. Update `backend/main.py` (Already Done ✅)
CORS middleware must be added BEFORE auth middleware.

### 2. Update `.env.local`

```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 3. Restart Backend
```powershell
# Kill old process (Ctrl+C)
# Then restart:
python -m uvicorn backend.main:app --reload --port 8000
```

### 4. Frontend Must Send Auth Header

```typescript
// When calling API endpoints:
const token = localStorage.getItem('auth_token');

const response = await fetch('http://localhost:8000/api/v1/assessment/status', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

---

## Verify It's Fixed

```powershell
# 1. Health check (no auth needed)
curl http://localhost:8000/health

# Expected: 200 OK ✓

# 2. Check CORS headers (OPTIONS request)
curl -X OPTIONS `
  -H "Origin: http://localhost:3000" `
  -H "Access-Control-Request-Method: GET" `
  http://localhost:8000/api/v1/assessment/status

# Expected to see in response:
# Access-Control-Allow-Origin: http://localhost:3000 ✓
# Access-Control-Allow-Credentials: true ✓
```

---

## Why This Happens

- **CORS headers** sent only by CORS middleware
- **Auth validation** happens in auth middleware
- If auth runs first → error returned before CORS headers added
- **Solution**: CORS middleware must run after auth completes (reverse middleware order in Starlette)

---

## Troubleshooting Matrix

| Symptom | Likely Cause | Check |
|---------|------------|-------|
| 401 Unauthorized | No/invalid token | `localStorage.getItem('auth_token')` |
| 500 Internal Server | Backend error | `curl http://localhost:8000/health` |
| Net::ERR_FAILED | Backend not running | `netstat -an \| findstr :8000` |
| 404 Not Found | Wrong endpoint | Check URL in browser Network tab |
| No `Access-Control-Allow-*` headers | CORS config issue | Check `.env.local` CORS_ALLOWED_ORIGINS |

---

## Files Modified

- ✅ `backend/main.py` - Middleware order fixed
- ✅ `.env.example` - CORS configuration documented
- 📝 Create `.env.local` with CORS_ALLOWED_ORIGINS set

---

*See [CORS_AND_AUTH_TROUBLESHOOTING.md](CORS_AND_AUTH_TROUBLESHOOTING.md) for detailed guide.*
