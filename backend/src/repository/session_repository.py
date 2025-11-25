from abc import ABC, abstractmethod

from domains import Session
from injector import singleton
from repository.base_exception import BaseRepositoryError
from repository.decorators import handle_repository_errors
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


class SessionRepositoryError(BaseRepositoryError):
    """セッションリポジトリ例外クラス"""

    pass


class SessionCreateError(SessionRepositoryError):
    """セッション作成時のエラー"""

    pass


class SessionQueryError(SessionRepositoryError):
    """セッションクエリ実行時のエラー"""

    pass


class SessionRepositoryIf(ABC):
    """セッションリポジトリインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @abstractmethod
    async def create_session(
        self, session: AsyncSession, session_data: Session
    ) -> Session:
        """セッションを作成する

        Args:
            session (AsyncSession): データベースセッション
            session_data (Session): セッションデータ

        Returns:
            Session: 作成されたセッション
        """

        pass

    @abstractmethod
    async def get_session_by_refresh_token(
        self, session: AsyncSession, token: str
    ) -> Session | None:
        """リフレッシュトークンからセッションを取得する

        Args:
            session (AsyncSession): データベースセッション
            token (str): セッショントークン

        Returns:
            Session | None: 取得されたセッション(見つからない場合はNone)
        """

        pass

    @abstractmethod
    async def get_session_by_access_token(
        self, session: AsyncSession, access_token: str
    ) -> Session | None:
        """アクセストークンからセッションを取得する

        Args:
            session (AsyncSession): データベースセッション
            access_token (str): アクセストークン

        Returns:
            Session | None: 取得されたセッション(見つからない場合はNone)
        """

        pass


@singleton
class SessionRepositoryImpl(SessionRepositoryIf):
    """セッションリポジトリ実装

    Args:
        SessionRepositoryIf (_type_): セッションリポジトリインターフェース
    """

    @handle_repository_errors(SessionCreateError, "セッション作成")
    async def create_session(
        self, session: AsyncSession, session_data: Session
    ) -> Session:
        """セッションを作成する

        Args:
            session (AsyncSession): データベースセッション
            session_data (Session): セッションデータ

        Returns:
            Session: 作成されたセッション
        """

        session.add(session_data)
        await session.commit()
        await session.refresh(session_data)

        return session_data

    @handle_repository_errors(SessionQueryError, "セッション取得")
    async def get_session_by_refresh_token(
        self, session: AsyncSession, token: str
    ) -> Session | None:
        """リフレッシュトークンからセッションを取得する

        Args:
            session (AsyncSession): データベースセッション
            token (str): セッショントークン

        Returns:
            Session | None: 取得されたセッション（見つからない場合はNone）
        """

        result = await session.execute(
            select(Session).where(Session.refresh_token == token)
        )

        return result.scalars().first()

    @handle_repository_errors(SessionQueryError, "セッション取得")
    async def get_session_by_access_token(
        self, session: AsyncSession, access_token: str
    ) -> Session | None:
        """アクセストークンからセッションを取得する

        Args:
            session (AsyncSession): データベースセッション
            access_token (str): アクセストークン

        Returns:
            Session | None: 取得されたセッション（見つからない場合はNone）
        """

        result = await session.execute(
            select(Session).where(Session.access_token == access_token)
        )

        return result.scalars().first()
