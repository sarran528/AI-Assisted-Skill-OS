from typing import Callable
import logging

from fastapi import Request, Response
from jose import JWTError, ExpiredSignatureError

from backend.auth.jwt_handler import decode_access_token

logger = logging.getLogger(__name__)


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
        except ExpiredSignatureError:
            logger.warning(f"Expired token used for request: {request.method} {request.url.path}")
            # Let auth dependency handle the expired token with proper error response
        except JWTError as e:
            logger.warning(f"Invalid token used for request: {request.method} {request.url.path} - Error: {str(e)}")
            # Let auth dependency perform authoritative token validation
        except ValueError as e:
            logger.warning(f"Malformed token used for request: {request.method} {request.url.path} - Error: {str(e)}")
            # Let auth dependency perform authoritative token validation
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {request.method} {request.url.path} - Error: {str(e)}")
            # Let auth dependency perform authoritative token validation

    return await call_next(request)
