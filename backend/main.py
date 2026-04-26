import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware

# Ensure the parent directory is in sys.path so 'import backend' works
# regardless of whether you run from the root or inside the backend folder.
backend_root = Path(__file__).resolve().parent
if str(backend_root.parent) not in sys.path:
    sys.path.insert(0, str(backend_root.parent))

# Vercel Root Fix: If 'backend' is the root, 'import backend' might fail.
# We map the current directory to 'sys.modules["backend"]' to fix this.
try:
    import backend
except ImportError:
    import sys
    import types
    backend_mock = types.ModuleType("backend")
    backend_mock.__path__ = [str(backend_root)]
    sys.modules["backend"] = backend_mock
    # Re-import to ensure it's available
    import backend

from backend.api.router import api_router
from backend.user.router import router as user_router
from backend.shared.config import settings
from backend.shared.errors import BusinessError, SystemError
from backend.auth.middleware import auth_context_middleware
from backend.shared.logging import configure_logging
from backend.shared.rate_limit import limiter
from backend.shared.middleware import request_id_middleware


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="SkillOS", version="0.1.0")
    app.state.limiter = limiter
    app.middleware("http")(request_id_middleware)
    app.middleware("http")(auth_context_middleware)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip().rstrip('/') for o in settings.cors_allowed_origins.split(",")],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
        allow_credentials=True,
    )

    @app.exception_handler(BusinessError)
    async def business_error_handler(_request: Request, exc: BusinessError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"code": exc.code, "message": str(exc), "context": exc.context},
        )

    @app.exception_handler(SystemError)
    async def system_error_handler(_request: Request, exc: SystemError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"code": "system_error", "message": "Unexpected error"},
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(status_code=429, content={"code": "rate_limited", "message": str(exc)})

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/.well-known/jwks.json")
    async def well_known_jwks() -> dict:
        import json
        # Look inside the backend folder for .well-known
        jwks_path = Path(__file__).resolve().parent / ".well-known" / "jwks.json"
        if jwks_path.exists():
            return json.loads(jwks_path.read_text(encoding="utf-8"))
        return {"keys": []}

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(user_router, prefix="/api/v1")
    return app


app = create_app()
