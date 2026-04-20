from typing import Callable

from fastapi import Request, Response
from jose import JWTError

from backend.auth.jwt_handler import decode_access_token


async def auth_context_middleware(request: Request, call_next: Callable) -> Response:
    request.state.user_id = None

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_access_token(token)
            subject = payload.get("sub")
            if subject:
                request.state.user_id = str(subject)
        except (JWTError, ValueError):
            # Let auth dependency perform authoritative token validation.
            pass

    return await call_next(request)
