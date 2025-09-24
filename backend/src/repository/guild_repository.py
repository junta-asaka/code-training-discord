from abc import ABC, abstractmethod

from domains import Guild
from injector import singleton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


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


@singleton
class GuildRepositoryImpl(GuildRepositoryIf):
    """ギルドリポジトリ実装

    Args:
        GuildRepositoryIf (_type_): ギルドリポジトリインターフェース
    """

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
