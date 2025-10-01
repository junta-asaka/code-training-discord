from abc import ABC, abstractmethod

from domains import Friend
from injector import singleton
from repository.base_exception import BaseRepositoryError
from repository.decorators import handle_repository_errors
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


class FriendRepositoryError(BaseRepositoryError):
    """フレンドリポジトリ例外クラス"""

    pass


class FriendCreateError(FriendRepositoryError):
    """フレンド作成時のエラー"""

    pass


class FriendQueryError(FriendRepositoryError):
    """フレンドクエリ実行時のエラー"""

    pass


class FriendRepositoryIf(ABC):
    """フレンドリポジトリインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @abstractmethod
    async def create_friend(self, session: AsyncSession, friend: Friend) -> Friend:
        """フレンドを作成する

        Args:
            session (AsyncSession): データベースセッション
            friend (Friend): 作成するフレンド情報

        Returns:
            Friend: 作成されたフレンド情報
        """

        pass

    @abstractmethod
    async def get_friend_all(self, session: AsyncSession, user_id: str) -> list[Friend]:
        """すべてのフレンドを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_id (str): ユーザーID

        Returns:
            list[Friend]: フレンドリスト
        """

        pass


@singleton
class FriendRepositoryImpl(FriendRepositoryIf):
    """フレンドリポジトリ実装

    Args:
        FriendRepositoryIf (_type_): フレンドリポジトリインターフェース
    """

    @handle_repository_errors(FriendCreateError, "フレンド作成")
    async def create_friend(self, session: AsyncSession, friend: Friend) -> Friend:
        """フレンドを作成する

        Args:
            session (AsyncSession): データベースセッション
            friend (Friend): 作成するフレンド情報

        Returns:
            Friend: 作成されたフレンド情報
        """

        session.add(friend)
        await session.commit()
        await session.refresh(friend)

        return friend

    @handle_repository_errors(FriendQueryError, "フレンド取得")
    async def get_friend_all(self, session: AsyncSession, user_id: str) -> list[Friend]:
        """すべてのフレンドを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_id (str): ユーザーID

        Returns:
            list[Friend]: フレンドリスト
        """

        result = await session.execute(
            select(Friend)
            .where(or_(Friend.user_id == user_id, Friend.related_user_id == user_id))
            .order_by(Friend.created_at.desc())  # 作成日時で降順ソート
        )

        return list(result.scalars().all())
