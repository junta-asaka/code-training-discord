from abc import ABC, abstractmethod

from domains import Session
from injector import singleton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class SessionRepositoryIf(ABC):
    @abstractmethod
    async def create_session(self, session: AsyncSession, session_data: Session) -> Session:
        pass

    @abstractmethod
    async def get_session_by_token(self, session: AsyncSession, token: str) -> Session:
        pass


@singleton
class SessionRepositoryImpl(SessionRepositoryIf):
    async def create_session(self, session: AsyncSession, session_data: Session) -> Session:
        session_db = Session(
            user_id=session_data.user_id,
            refresh_token_hash=session_data.refresh_token_hash,
            user_agent=session_data.user_agent,
            ip_address=session_data.ip_address,
            revoked_at=session_data.revoked_at,
        )

        session.add(session_db)
        await session.commit()
        await session.refresh(session_db)

        return session_db

    async def get_session_by_token(self, session: AsyncSession, token: str) -> Session:
        result = await session.execute(select(Session).where(Session.refresh_token_hash == token))

        return result.scalars().first()
