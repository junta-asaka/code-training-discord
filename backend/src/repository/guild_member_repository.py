from abc import ABC, abstractmethod

from domains import GuildMember
from injector import singleton
from repository.base_exception import BaseRepositoryError
from repository.decorators import handle_repository_errors
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


class GuildMemberRepositoryError(BaseRepositoryError):
    """ギルドメンバーリポジトリ例外クラス"""

    pass


class GuildMemberCreateError(GuildMemberRepositoryError):
    """ギルドメンバー作成時のエラー"""

    pass


class GuildMemberRepositoryIf(ABC):
    """ギルドメンバーリポジトリインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @abstractmethod
    async def create_guild_member(
        self, session: AsyncSession, guild_member: GuildMember
    ) -> GuildMember:
        """ギルドメンバーを作成する

        Args:
            session (AsyncSession): データベースセッション
            guild_member (GuildMember): 作成するギルドメンバー情報

        Returns:
            GuildMember: 作成されたギルドメンバー情報
        """

        pass


@singleton
class GuildMemberRepositoryImpl(GuildMemberRepositoryIf):
    """ギルドメンバーリポジトリ実装

    Args:
        GuildMemberRepositoryIf (_type_): ギルドメンバーリポジトリインターフェース
    """

    @handle_repository_errors(GuildMemberCreateError, "ギルドメンバー作成")
    async def create_guild_member(
        self, session: AsyncSession, guild_member: GuildMember
    ) -> GuildMember:
        """ギルドメンバーを作成する

        Args:
            session (AsyncSession): データベースセッション
            guild_member (GuildMember): 作成するギルドメンバー情報

        Returns:
            GuildMember: 作成されたギルドメンバー情報
        """

        session.add(guild_member)
        await session.flush()  # commit の代わりに flush を使用（IDを取得するため）
        await session.refresh(guild_member)

        return guild_member
