import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware

from backend.api.router import api_router
from backend.user.router import router as user_router
from backend.shared.config import settings
from backend.shared.errors import BusinessError, SystemError
from backend.auth.middleware import auth_context_middleware
from backend.shared.db.session import get_db_session
from sqlalchemy import text
import redis

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
        allow_origins=settings.cors_allowed_origins.split(","),
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
    async def health() -> dict[str, Any]:
        health_status = {"status": "ok", "database": "unknown", "redis": "unknown"}
        
        # Check Database
        try:
            async for session in get_db_session():
                await session.execute(text("SELECT 1"))
                health_status["database"] = "connected"
                break
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
            health_status["status"] = "error"

        # Check Redis
        try:
            r = redis.from_url(settings.redis_url)
            if r.ping():
                health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
            health_status["status"] = "error"

        return health_status

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/.well-known/jwks.json")
    async def well_known_jwks() -> dict:
        jwks_path = Path(__file__).resolve().parents[1] / ".well-known" / "jwks.json"
        if jwks_path.exists():
            return json.loads(jwks_path.read_text(encoding="utf-8"))
        return {"keys": []}

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(user_router, prefix="/api/v1")
    return app


app = create_app()
