from abc import ABC, abstractmethod

from domains import Message
from injector import singleton
from repository.base_exception import BaseRepositoryError
from repository.decorators import handle_repository_errors
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


class MessageRepositoryError(BaseRepositoryError):
    """メッセージリポジトリ例外クラス"""

    pass


class MessageCreateError(MessageRepositoryError):
    """メッセージ作成時のエラー"""

    pass


class MessageQueryError(MessageRepositoryError):
    """メッセージクエリ実行時のエラー"""

    pass


class MessageRepositoryIf(ABC):
    """メッセージリポジトリインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @abstractmethod
    async def create_message(self, session: AsyncSession, message: Message) -> Message:
        """メッセージを作成する

        Args:
            session (AsyncSession): データベースセッション
            message (Message): 作成するメッセージ情報

        Returns:
            Message: 作成されたメッセージ情報
        """

        pass

    @abstractmethod
    async def get_message_by_channel_id(
        self, session: AsyncSession, channel_id: str
    ) -> list[Message]:
        """チャネルIDからメッセージを取得する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャネルID

        Returns:
            list[Message]: メッセージ情報のリスト
        """

        pass


@singleton
class MessageRepositoryImpl(MessageRepositoryIf):
    """メッセージリポジトリ実装

    Args:
        MessageRepositoryIf (_type_): メッセージリポジトリインターフェース
    """

    @handle_repository_errors(MessageCreateError, "メッセージ作成")
    async def create_message(self, session: AsyncSession, message: Message) -> Message:
        """メッセージを作成する

        Args:
            session (AsyncSession): データベースセッション
            message (Message): 作成するメッセージ情報

        Returns:
            Message: 作成されたメッセージ情報
        """

        session.add(message)
        await session.flush()  # commit の代わりに flush を使用（IDを取得するため）
        await session.refresh(message)
        logger.info(
            f"メッセージが正常に作成されました: message_id={message.id}, channel_id={message.channel_id}"
        )

        return message

    @handle_repository_errors(MessageQueryError, "メッセージ取得")
    async def get_message_by_channel_id(
        self, session: AsyncSession, channel_id: str
    ) -> list[Message]:
        """チャネルIDからメッセージを取得する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャネルID

        Returns:
            list[Message]: メッセージ情報のリスト
        """

        result = await session.execute(
            select(Message)
            .where(Message.channel_id == channel_id)
            .order_by(Message.created_at)
        )
        messages = list(result.scalars().all())
        logger.info(
            f"チャネル {channel_id} のメッセージを {len(messages)} 件取得しました"
        )

        return messages
