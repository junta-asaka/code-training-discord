from abc import ABC, abstractmethod

from domains import GuildMember
from injector import singleton
from sqlalchemy.ext.asyncio import AsyncSession


class GuildMemberRepositoryIf(ABC):
    """ギルドメンバーリポジトリインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @abstractmethod
    async def create_guild_member(self, session: AsyncSession, guild_member: GuildMember) -> GuildMember:
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

    async def create_guild_member(self, session: AsyncSession, guild_member: GuildMember) -> GuildMember:
        """ギルドメンバーを作成する

        Args:
            session (AsyncSession): データベースセッション
            guild_member (GuildMember): 作成するギルドメンバー情報

        Returns:
            GuildMember: 作成されたギルドメンバー情報
        """

        session.add(guild_member)
        await session.commit()
        await session.refresh(guild_member)

        return guild_member
