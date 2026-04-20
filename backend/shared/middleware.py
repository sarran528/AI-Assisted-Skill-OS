import uuid
from typing import Callable

from fastapi import Request, Response

from backend.shared.logging import request_id_ctx, user_id_ctx


async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    request.state.request_id = request_id
    request_id_ctx.set(request_id)
    user_id_ctx.set("")
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response
