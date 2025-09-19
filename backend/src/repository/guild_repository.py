from abc import ABC, abstractmethod

from domains import Guild
from injector import singleton
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
