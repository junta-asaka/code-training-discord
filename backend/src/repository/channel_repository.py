from abc import ABC, abstractmethod
from typing import Optional

from domains import Channel
from injector import singleton
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


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

        Raises:
            SQLAlchemyError: データベースエラーが発生した場合
            Exception: その他の予期しないエラーが発生した場合
        """

        pass

    @abstractmethod
    async def get_channel_by_guild_ids(self, session: AsyncSession, guild_id: str, related_guild_id: str) -> Channel:
        """ギルドIDと関連ギルドIDからチャネルを取得する

        Args:
            session (AsyncSession): データベースセッション
            guild_id (str): ギルドID
            related_guild_id (str): 関連ギルドID

        Returns:
            Channel: チャネル
        """

        pass

    @abstractmethod
    async def get_channel_by_id(self, session: AsyncSession, channel_id: str) -> Optional[Channel]:
        """チャネルIDからチャネルを取得する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャネルID

        Returns:
            Optional[Channel]: チャネル（存在しない場合はNone）
        """
        pass

    # last_message_idの更新メソッド
    @abstractmethod
    async def update_last_message_id(self, session: AsyncSession, channel_id: str, last_message_id: str) -> None:
        """チャネルのlast_message_idを更新する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャネルID
            last_message_id (str): 更新するlast_message_id

        Raises:
            SQLAlchemyError: データベースエラーが発生した場合
            Exception: その他の予期しないエラーが発生した場合
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

        Raises:
            SQLAlchemyError: データベースエラーが発生した場合
            Exception: その他の予期しないエラーが発生した場合
        """

        try:
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            return channel
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"チャネル作成中にDBエラー発生: {e}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"チャネル作成中に予期しないエラー発生: {e}")
            raise

    async def get_channel_by_guild_ids(self, session: AsyncSession, guild_id: str, related_guild_id: str) -> Channel:
        """ギルドIDと関連ギルドIDからチャネルを取得する

        Args:
            session (AsyncSession): データベースセッション
            guild_id (str): ギルドID
            related_guild_id (str): 関連ギルドID

        Returns:
            Channel: チャネル
        """

        result = await session.execute(
            select(Channel).where(Channel.guild_id == guild_id, Channel.related_guild_id == related_guild_id)
        )

        return result.scalars().first()

    async def get_channel_by_id(self, session: AsyncSession, channel_id: str) -> Optional[Channel]:
        """チャネルIDからチャネルを取得する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャネルID

        Returns:
            Optional[Channel]: チャネル（存在しない場合はNone）
        """

        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        return result.scalars().first()

    async def update_last_message_id(self, session: AsyncSession, channel_id: str, last_message_id: str) -> None:
        """チャネルのlast_message_idを更新する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャネルID
            last_message_id (str): 更新するlast_message_id

        Raises:
            SQLAlchemyError: データベースエラーが発生した場合
            Exception: その他の予期しないエラーが発生した場合
        """

        try:
            await session.execute(
                update(Channel).where(Channel.id == channel_id).values(last_message_id=last_message_id)
            )
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"チャネルのlast_message_id更新中にDBエラー発生: {e}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"チャネルのlast_message_id更新中に予期しないエラー発生: {e}")
            raise
