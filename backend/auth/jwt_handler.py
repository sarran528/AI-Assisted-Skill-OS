import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Union

from jose import jwt

from backend.shared.config import settings

ALGORITHM = "RS256"


def _load_jwks() -> dict[str, Any]:
    jwks_path = Path(__file__).resolve().parents[2] / ".well-known" / "jwks.json"
    if jwks_path.exists():
        return json.loads(jwks_path.read_text(encoding="utf-8"))
    return {"keys": []}


def get_public_key_for_kid(kid: str) -> Union[str, dict[str, Any]]:
    jwks = _load_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    if kid == settings.jwt_kid:
        return settings.jwt_public_key
    raise ValueError("Unknown key id")


def create_access_token(user_id: str, email: str, status: str) -> tuple[str, str, datetime]:
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.jwt_access_ttl)
    payload = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": user_id,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "email": email,
        "status": status,
    }
    token = jwt.encode(payload, settings.jwt_private_key, algorithm=ALGORITHM, headers={"kid": settings.jwt_kid})
    return token, jti, exp


def decode_access_token(token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if not kid:
        raise ValueError("Missing kid")
    public_key = get_public_key_for_kid(kid)
    payload = jwt.decode(
        token,
        public_key,
        algorithms=[ALGORITHM],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
    return payload
