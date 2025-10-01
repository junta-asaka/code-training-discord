from abc import ABC, abstractmethod
from typing import Optional

from domains import Channel
from injector import singleton
from repository.base_exception import BaseRepositoryError
from repository.decorators import handle_repository_errors
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


class ChannelRepositoryError(BaseRepositoryError):
    """チャンネルリポジトリ例外クラス"""

    pass


class ChannelCreateError(ChannelRepositoryError):
    """チャンネル作成時のエラー"""

    pass


class ChannelQueryError(ChannelRepositoryError):
    """チャンネルクエリ実行時のエラー"""

    pass


class ChannelUpdateError(ChannelRepositoryError):
    """チャンネル更新時のエラー"""

    pass


class ChannelNotFoundError(ChannelRepositoryError):
    """チャンネルが見つからない場合のエラー"""

    pass


class ChannelRepositoryIf(ABC):
    """チャンネルリポジトリインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @abstractmethod
    async def create_channel(self, session: AsyncSession, channel: Channel) -> Channel:
        """チャンネルを作成する

        Args:
            session (AsyncSession): データベースセッション
            channel (Channel): 作成するチャンネル情報

        Returns:
            Channel: 作成されたチャンネル情報
        """

        pass

    @abstractmethod
    async def get_channel_by_id(self, session: AsyncSession, channel_id: str) -> Optional[Channel]:
        """チャンネルIDからチャンネルを取得する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャンネルID

        Returns:
            Optional[Channel]: チャンネル（存在しない場合はNone）
        """

        pass

    # last_message_idの更新メソッド
    @abstractmethod
    async def update_last_message_id(self, session: AsyncSession, channel_id: str, last_message_id: str) -> None:
        """チャンネルのlast_message_idを更新する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャンネルID
            last_message_id (str): 更新するlast_message_id
        """

        pass


@singleton
class ChannelRepositoryImpl(ChannelRepositoryIf):
    """チャンネルリポジトリ実装

    Args:
        ChannelRepositoryIf (_type_): チャンネルリポジトリインターフェース
    """

    @handle_repository_errors(ChannelCreateError, "チャンネル作成")
    async def create_channel(self, session: AsyncSession, channel: Channel) -> Channel:
        """チャンネルを作成する

        Args:
            session (AsyncSession): データベースセッション
            channel (Channel): 作成するチャンネル情報

        Returns:
            Channel: 作成されたチャンネル情報
        """

        session.add(channel)
        await session.commit()
        await session.refresh(channel)
        logger.info(f"チャンネルが正常に作成されました: channel_id={channel.id}, guild_id={channel.guild_id}")

        return channel

    @handle_repository_errors(ChannelQueryError, "チャンネルIDによるチャンネル取得")
    async def get_channel_by_id(self, session: AsyncSession, channel_id: str) -> Optional[Channel]:
        """チャンネルIDからチャンネルを取得する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャンネルID

        Returns:
            Optional[Channel]: チャンネル（存在しない場合はNone）
        """

        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalars().first()

        if channel:
            logger.info(f"チャンネルが見つかりました: channel_id={channel_id}")
        else:
            logger.info(f"チャンネルが見つかりませんでした: channel_id={channel_id}")

        return channel

    @handle_repository_errors(ChannelUpdateError, "チャンネルのlast_message_id更新")
    async def update_last_message_id(self, session: AsyncSession, channel_id: str, last_message_id: str) -> None:
        """チャンネルのlast_message_idを更新する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャンネルID
            last_message_id (str): 更新するlast_message_id

        Raises:
            ChannelNotFoundError: 指定されたチャンネルが存在しない場合
        """

        result = await session.execute(
            update(Channel).where(Channel.id == channel_id).values(last_message_id=last_message_id)
        )

        # 更新された行数をチェック
        if result.rowcount == 0:
            error_msg = f"指定されたチャンネルが存在しません: channel_id={channel_id}"
            logger.warning(error_msg)
            raise ChannelNotFoundError(error_msg)

        logger.info(
            f"チャンネルのlast_message_idが正常に更新されました: channel_id={channel_id}, last_message_id={last_message_id}"
        )
