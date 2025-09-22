from abc import ABC, abstractmethod

from domains import Session
from injector import singleton
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


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

        try:
            session.add(session_data)
            await session.commit()
            await session.refresh(session_data)
            return session_data
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"セッション作成中にDBエラー発生: {e}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"セッション作成中に予期しないエラー発生: {e}")
            raise

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
