from typing import Callable

from fastapi import Request, Response


async def auth_context_middleware(request: Request, call_next: Callable) -> Response:
    request.state.user_id = None
    return await call_next(request)
