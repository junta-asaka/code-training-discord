from abc import ABC, abstractmethod

from domains import Session
from injector import singleton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class SessionRepositoryIf(ABC):
    """セッションリポジトリインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @abstractmethod
    async def create_session(self, session: AsyncSession, session_data: Session) -> Session:
        """セッションを作成する

        Args:
            session (AsyncSession): データベースセッション
            session_data (Session): セッションデータ

        Returns:
            Session: 作成されたセッション
        """

        pass

    @abstractmethod
    async def get_session_by_token(self, session: AsyncSession, token: str) -> Session:
        """トークンからセッションを取得する

        Args:
            session (AsyncSession): データベースセッション
            token (str): セッショントークン

        Returns:
            Session: 取得されたセッション
        """

        pass


@singleton
class SessionRepositoryImpl(SessionRepositoryIf):
    """セッションリポジトリ実装

    Args:
        SessionRepositoryIf (_type_): セッションリポジトリインターフェース
    """

    async def create_session(self, session: AsyncSession, session_data: Session) -> Session:
        """セッションを作成する

        Args:
            session (AsyncSession): データベースセッション
            session_data (Session): セッションデータ

        Returns:
            Session: 作成されたセッション
        """

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
        """トークンからセッションを取得する

        Args:
            session (AsyncSession): データベースセッション
            token (str): セッショントークン

        Returns:
            Session: 取得されたセッション
        """

        result = await session.execute(select(Session).where(Session.refresh_token_hash == token))

        return result.scalars().first()
