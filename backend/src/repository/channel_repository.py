from abc import ABC, abstractmethod
from typing import Optional

from domains import Channel, Guild, GuildMember
from injector import singleton
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession


class ChannelRepositoryIf(ABC):
    """チャネルリポジトリインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @abstractmethod
    async def create_channel(self, session: AsyncSession, channel: Channel) -> Channel:
        """チャネルを作成する

        Args:
            session (AsyncSession): データベースセッション
            channel (Channel): 作成するチャネル情報

        Returns:
            Channel: 作成されたチャネル情報
        """

        pass

    @abstractmethod
    async def get_channels_by_user_ids_type_name(
        self,
        session: AsyncSession,
        user_ids: list[str],
        type: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Channel:
        """指定したユーザーIDを含むギルドのチャネルを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_ids (list[str]): ユーザーIDのリスト
            type (Optional[str]): チャネルタイプ
            name (Optional[str]): チャネル名

        Returns:
            Channel: チャネル
        """

        pass


@singleton
class ChannelRepositoryImpl(ChannelRepositoryIf):
    """チャネルリポジトリ実装

    Args:
        ChannelRepositoryIf (_type_): チャネルリポジトリインターフェース
    """

    async def create_channel(self, session: AsyncSession, channel: Channel) -> Channel:
        """チャネルを作成する

        Args:
            session (AsyncSession): データベースセッション
            channel (Channel): 作成するチャネル情報

        Returns:
            Channel: 作成されたチャネル情報
        """

        session.add(channel)
        await session.commit()
        await session.refresh(channel)

        return channel

    async def get_channels_by_user_ids_type_name(
        self,
        session: AsyncSession,
        user_ids: list[str],
        type: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Channel:
        """指定したユーザーIDを含むギルドのチャネルを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_ids (list[str]): ユーザーIDのリスト
            type (Optional[str]): チャネルタイプ
            name (Optional[str]): チャネル名

        Returns:
            Channel: チャネル
        """

        # 基本的なJOIN条件を構築
        query = (
            select(Channel)
            .join(Guild, Channel.guild_id == Guild.id)
            .join(GuildMember, Guild.id == GuildMember.guild_id)
            .where(GuildMember.user_id.in_(user_ids))
        )

        # 追加の条件を動的に構築
        conditions = []
        if type is not None:
            conditions.append(Channel.type == type)
        if name is not None:
            conditions.append(Channel.name == name)

        # 条件がある場合は追加
        if conditions:
            query = query.where(and_(*conditions))

        # 重複を除去
        query = query.distinct()

        result = await session.execute(query)
        return result.scalars().first()
