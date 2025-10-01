from abc import ABC, abstractmethod
from typing import Optional

from domains import Channel, Guild, GuildMember
from injector import singleton
from repository.base_exception import BaseRepositoryError
from repository.decorators import handle_repository_errors
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


class GuildRepositoryError(BaseRepositoryError):
    """ギルドリポジトリ例外クラス"""

    pass


class GuildCreateError(GuildRepositoryError):
    """ギルド作成時のエラー"""

    pass


class GuildQueryError(GuildRepositoryError):
    """ギルドクエリ実行時のエラー"""

    pass


class GuildRepositoryIf(ABC):
    """ギルドリポジトリインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @abstractmethod
    async def create_guild(self, session: AsyncSession, guild: Guild) -> Guild:
        """ギルドを作成する

        Args:
            session (AsyncSession): データベースセッション
            guild (Guild): 作成するギルド情報

        Returns:
            Guild: 作成されたギルド情報
        """

        pass

    @abstractmethod
    async def get_guild_by_user_id_name(self, session: AsyncSession, user_id: str, name: str) -> Guild:
        """idとギルド名からギルドを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_id (str): ギルドのオーナーのユーザーID
            name (str): ギルド名

        Returns:
            Guild: ギルド情報
        """
        pass

    @abstractmethod
    async def get_guild_by_member_channel(
        self, session: AsyncSession, member_id: str, channel_id: str
    ) -> Optional[Guild]:
        """ギルドメンバーIDとチャネルIDを条件指定し、ギルド情報を取得する

        Args:
            session (AsyncSession): データベースセッション
            member_id (str): ギルドメンバーのユーザーID
            channel_id (str): チャネルID

        Returns:
            Optional[Guild]: ギルド情報
        """

        pass


@singleton
class GuildRepositoryImpl(GuildRepositoryIf):
    """ギルドリポジトリ実装

    Args:
        GuildRepositoryIf (_type_): ギルドリポジトリインターフェース
    """

    @handle_repository_errors(GuildCreateError, "ギルド作成")
    async def create_guild(self, session: AsyncSession, guild: Guild) -> Guild:
        """ギルドを作成する

        Args:
            session (AsyncSession): データベースセッション
            guild (Guild): 作成するギルド情報

        Returns:
            Guild: 作成されたギルド情報
        """

        session.add(guild)
        await session.commit()
        await session.refresh(guild)

        return guild

    @handle_repository_errors(GuildQueryError, "ギルド取得")
    async def get_guild_by_user_id_name(self, session: AsyncSession, user_id: str, name: str) -> Guild:
        """idとギルド名からギルドを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_id (str): ギルドのオーナーのユーザーID
            name (str): ギルド名

        Returns:
            Guild: ギルド情報
        """

        result = await session.execute(select(Guild).where(Guild.owner_user_id == user_id, Guild.name == name))

        return result.scalars().first()

    @handle_repository_errors(GuildQueryError, "ギルド取得")
    async def get_guild_by_member_channel(
        self, session: AsyncSession, member_id: str, channel_id: str
    ) -> Optional[Guild]:
        """ギルドメンバーIDとチャネルIDを条件指定し、ギルド情報を取得する

        Args:
            session (AsyncSession): データベースセッション
            member_id (str): ギルドメンバーのユーザーID
            channel_id (str): チャネルID

        Returns:
            Optional[Guild]: ギルド情報
        """

        result = await session.execute(
            select(Guild)
            .join(GuildMember)
            .join(Channel)
            .where(GuildMember.user_id == member_id, Channel.id == channel_id)
        )
        guild = result.scalars().first()

        if guild:
            logger.info(f"ギルドが見つかりました: member_id={member_id}, channel_id={channel_id}")
        else:
            logger.info(f"ギルドが見つかりませんでした: member_id={member_id}, channel_id={channel_id}")

        return guild
