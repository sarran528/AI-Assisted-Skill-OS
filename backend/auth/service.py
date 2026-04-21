import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt_handler import create_access_token
from backend.auth.password import hash_password, verify_password
from backend.shared.audit import log_audit_event
from backend.shared.config import settings
from backend.shared.db.repositories.auth_repo import AuthRepository
from backend.shared.db.repositories.cognitive_profile_repo import CognitiveProfileRepository


COOKIE_NAME = "skillos_refresh"


def _hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _generate_refresh_token() -> str:
    return secrets.token_bytes(64).hex()


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="strict",
        secure=settings.app_env != "local",
        max_age=settings.jwt_refresh_ttl,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/api/v1/auth")


async def register_user(
    *,
    db_session: AsyncSession,
    email: str,
    password: str,
    response: Response,
    ip_address: str | None,
    user_agent: str | None,
) -> dict:
    repo = AuthRepository(db_session)
    existing = await repo.get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = await repo.create_user(email=email.lower(), password_hash=hash_password(password))
    
    cognitive_profile_repo = CognitiveProfileRepository(db_session)
    await cognitive_profile_repo.create_cognitive_profile(user.id)

    access_token, access_jti, access_exp = create_access_token(str(user.id), user.email, user.status)
    refresh_token = _generate_refresh_token()

    await repo.store_refresh_token(
        user_id=str(user.id),
        token_hash=_hash_refresh_token(refresh_token),
        jti=access_jti,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_refresh_ttl),
        ip_address=ip_address,
        user_agent=user_agent,
    )

    _set_refresh_cookie(response, refresh_token)
    await log_audit_event(
        db_session,
        user_id=str(user.id),
        action="auth.register",
        entity_type="user",
        entity_id=str(user.id),
        ip_address=ip_address,
    )
    return {"user_id": str(user.id), "email": user.email, "access_token": access_token}


async def login_user(
    *,
    db_session: AsyncSession,
    email: str,
    password: str,
    response: Response,
    ip_address: str | None,
    user_agent: str | None,
) -> dict:
    repo = AuthRepository(db_session)
    user = await repo.get_user_by_email(email.lower())
    if not user or not verify_password(password, user.password_hash):
        await log_audit_event(
            db_session,
            user_id=None,
            action="auth.login_failed",
            entity_type="user",
            entity_id=None,
            ip_address=ip_address,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User suspended")

    access_token, access_jti, access_exp = create_access_token(str(user.id), user.email, user.status)
    refresh_token = _generate_refresh_token()

    await repo.store_refresh_token(
        user_id=str(user.id),
        token_hash=_hash_refresh_token(refresh_token),
        jti=access_jti,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_refresh_ttl),
        ip_address=ip_address,
        user_agent=user_agent,
    )

    _set_refresh_cookie(response, refresh_token)
    await log_audit_event(
        db_session,
        user_id=str(user.id),
        action="auth.login",
        entity_type="user",
        entity_id=str(user.id),
        ip_address=ip_address,
    )
    return {"access_token": access_token}


async def refresh_tokens(
    *,
    db_session: AsyncSession,
    refresh_token: str,
    response: Response,
    ip_address: str | None,
    user_agent: str | None,
) -> dict:
    repo = AuthRepository(db_session)
    token_hash = _hash_refresh_token(refresh_token)
    stored = await repo.get_refresh_token(token_hash)

    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if stored.revoked_at is not None:
        await repo.revoke_all_refresh_tokens(str(stored.user_id))
        await log_audit_event(
            db_session,
            user_id=str(stored.user_id),
            action="auth.token_rotated",
            entity_type="user",
            entity_id=str(stored.user_id),
            ip_address=ip_address,
            metadata={"reason": "reuse_detected"},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    if stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = await repo.get_user_by_id(str(stored.user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token, access_jti, access_exp = create_access_token(str(user.id), user.email, user.status)
    new_refresh_token = _generate_refresh_token()

    await repo.revoke_refresh_token(str(stored.id))
    await repo.store_refresh_token(
        user_id=str(user.id),
        token_hash=_hash_refresh_token(new_refresh_token),
        jti=access_jti,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_refresh_ttl),
        ip_address=ip_address,
        user_agent=user_agent,
    )

    _set_refresh_cookie(response, new_refresh_token)
    await log_audit_event(
        db_session,
        user_id=str(user.id),
        action="auth.token_rotated",
        entity_type="user",
        entity_id=str(user.id),
        ip_address=ip_address,
    )
    return {"access_token": access_token}


async def logout_user(
    *,
    db_session: AsyncSession,
    access_jti: str,
    access_exp: int,
    user_id: str,
    refresh_token: str | None,
    response: Response,
    ip_address: str | None,
) -> None:
    repo = AuthRepository(db_session)
    expires_at = datetime.fromtimestamp(access_exp, tz=timezone.utc)
    await repo.add_revoked_access_token(access_jti, user_id, expires_at)

    if refresh_token:
        stored = await repo.get_refresh_token(_hash_refresh_token(refresh_token))
        if stored:
            await repo.revoke_refresh_token(str(stored.id))

    _clear_refresh_cookie(response)
    await log_audit_event(
        db_session,
        user_id=user_id,
        action="auth.logout",
        entity_type="user",
        entity_id=user_id,
        ip_address=ip_address,
    )


async def logout_all(
    *,
    db_session: AsyncSession,
    access_jti: str,
    access_exp: int,
    user_id: str,
    response: Response,
    ip_address: str | None,
) -> None:
    repo = AuthRepository(db_session)
    expires_at = datetime.fromtimestamp(access_exp, tz=timezone.utc)
    await repo.add_revoked_access_token(access_jti, user_id, expires_at)
    await repo.revoke_all_refresh_tokens(user_id)
    _clear_refresh_cookie(response)
    await log_audit_event(
        db_session,
        user_id=user_id,
        action="auth.logout",
        entity_type="user",
        entity_id=user_id,
        ip_address=ip_address,
        metadata={"scope": "all"},
    )
