from abc import ABC, abstractmethod

from domains import Channel, Friend, Guild, User
from injector import singleton
from repository.base_exception import BaseRepositoryError
from repository.decorators import handle_repository_errors
from sqlalchemy import Row, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
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
    async def get_friends_with_details(self, session: AsyncSession, user_id: str) -> list[Row]:
        """フレンド情報を関連テーブルと結合して取得する

        Args:
            session (AsyncSession): データベースセッション
            user_id (str): ユーザーID

        Returns:
            list[Row]: フレンド詳細情報のリスト
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
        await session.flush()  # commit の代わりに flush を使用（IDを取得するため）
        await session.refresh(friend)

        return friend

    @handle_repository_errors(FriendQueryError, "フレンド取得")
    async def get_friends_with_details(self, session: AsyncSession, user_id: str) -> list[Row]:
        """フレンド情報を関連テーブルと結合して取得する

        Args:
            session (AsyncSession): データベースセッション
            user_id (str): ユーザーID

        Returns:
            list[Row]: フレンド詳細情報のリスト
        """

        # エイリアスを作成
        my_guild = aliased(Guild)
        friend_guild = aliased(Guild)

        # JOINクエリを構築
        stmt = (
            select(
                User.name.label("user_name"),
                User.username.label("user_username"),
                User.description.label("user_description"),
                User.created_at.label("user_created_at"),
                Channel.id.label("channel_id"),
            )
            .select_from(Friend)
            .join(
                User,
                or_(
                    # 自分がuser_idの場合、相手はrelated_user_id
                    (Friend.user_id == user_id) & (User.id == Friend.related_user_id),
                    # 自分がrelated_user_idの場合、相手はuser_id
                    (Friend.related_user_id == user_id) & (User.id == Friend.user_id),
                ),
            )
            .join(my_guild, my_guild.owner_user_id == user_id)
            .join(friend_guild, friend_guild.owner_user_id == User.id)
            .join(
                Channel,
                or_(
                    # guild_id_me と guild_id_related の組み合わせ
                    (Channel.guild_id == my_guild.id) & (Channel.related_guild_id == friend_guild.id),
                    # guild_id_related と guild_id_me の組み合わせ（逆）
                    (Channel.guild_id == friend_guild.id) & (Channel.related_guild_id == my_guild.id),
                ),
            )
            .where(
                or_(Friend.user_id == user_id, Friend.related_user_id == user_id)
                & (my_guild.name == "@me")
                & (friend_guild.name == "@me")
            )
            .order_by(Friend.created_at.desc())
        )

        result = await session.execute(stmt)
        return list(result.fetchall())
