from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import RefreshToken, RevokedAccessToken, User


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash, status="active")
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def store_refresh_token(
        self,
        *,
        user_id: str,
        token_hash: str,
        jti: str,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            jti=jti,
            expires_at=expires_at,
            revoked_at=None,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self.session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_id: str) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.session.commit()

    async def revoke_all_refresh_tokens(self, user_id: str) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.session.commit()

    async def add_revoked_access_token(self, jti: str, user_id: str, expires_at: datetime) -> None:
        token = RevokedAccessToken(jti=jti, user_id=user_id, expires_at=expires_at)
        self.session.add(token)
        await self.session.commit()

    async def is_access_token_revoked(self, jti: str) -> bool:
        result = await self.session.execute(
            select(RevokedAccessToken).where(
                RevokedAccessToken.jti == jti,
                RevokedAccessToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none() is not None

    async def cleanup_refresh_tokens(self) -> None:
        await self.session.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc),
                RefreshToken.revoked_at.is_not(None),
            )
        )
        await self.session.commit()
