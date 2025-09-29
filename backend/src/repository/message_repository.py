from abc import ABC, abstractmethod

from domains import Message
from injector import singleton
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


class MessageRepositoryError(Exception):
    """メッセージリポジトリ基底例外クラス"""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class MessageCreateError(MessageRepositoryError):
    """メッセージ作成時のエラー"""

    pass


class MessageDatabaseConstraintError(MessageRepositoryError):
    """データベース制約違反エラー（外部キー制約など）"""

    pass


class MessageDatabaseConnectionError(MessageRepositoryError):
    """データベース接続エラー"""

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

        Raises:
            MessageDatabaseConstraintError: データベース制約違反の場合
            MessageDatabaseConnectionError: データベース接続エラーの場合
            MessageCreateError: メッセージ作成に失敗した場合
        """

        pass

    @abstractmethod
    async def get_message_by_channel_id(self, session: AsyncSession, channel_id: str) -> list[Message]:
        """チャネルIDからメッセージを取得する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャネルID

        Returns:
            list[Message]: メッセージ情報のリスト

        Raises:
            MessageDatabaseConnectionError: データベース接続エラーの場合
            MessageQueryError: クエリ実行に失敗した場合
        """

        pass


@singleton
class MessageRepositoryImpl(MessageRepositoryIf):
    """メッセージリポジトリ実装

    Args:
        MessageRepositoryIf (_type_): メッセージリポジトリインターフェース
    """

    async def create_message(self, session: AsyncSession, message: Message) -> Message:
        """メッセージを作成する

        Args:
            session (AsyncSession): データベースセッション
            message (Message): 作成するメッセージ情報

        Returns:
            Message: 作成されたメッセージ情報

        Raises:
            MessageDatabaseConstraintError: データベース制約違反の場合
            MessageDatabaseConnectionError: データベース接続エラーの場合
            MessageCreateError: メッセージ作成に失敗した場合
        """

        try:
            session.add(message)
            await session.flush()  # commit の代わりに flush を使用（IDを取得するため）
            await session.refresh(message)
            logger.info(f"メッセージが正常に作成されました: message_id={message.id}, channel_id={message.channel_id}")

            return message

        except IntegrityError as e:
            error_msg = f"データベース制約違反によりメッセージ作成に失敗: channel_id={message.channel_id}, user_id={message.user_id}"
            logger.error(f"{error_msg}: {e}")
            raise MessageDatabaseConstraintError(error_msg, e)

        except OperationalError as e:
            error_msg = f"データベース接続エラーによりメッセージ作成に失敗: channel_id={message.channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise MessageDatabaseConnectionError(error_msg, e)

        except SQLAlchemyError as e:
            error_msg = f"SQLAlchemyエラーによりメッセージ作成に失敗: channel_id={message.channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise MessageCreateError(error_msg, e)

        except Exception as e:
            error_msg = f"予期しないエラーによりメッセージ作成に失敗: channel_id={message.channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise MessageCreateError(error_msg, e)

    async def get_message_by_channel_id(self, session: AsyncSession, channel_id: str) -> list[Message]:
        """チャネルIDからメッセージを取得する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャネルID

        Returns:
            list[Message]: メッセージ情報のリスト

        Raises:
            MessageDatabaseConnectionError: データベース接続エラーの場合
            MessageQueryError: クエリ実行に失敗した場合
        """

        try:
            result = await session.execute(
                select(Message).where(Message.channel_id == channel_id).order_by(Message.created_at)
            )
            messages = list(result.scalars().all())
            logger.info(f"チャネル {channel_id} のメッセージを {len(messages)} 件取得しました")

            return messages

        except OperationalError as e:
            error_msg = f"データベース接続エラーによりメッセージ取得に失敗: channel_id={channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise MessageDatabaseConnectionError(error_msg, e)

        except SQLAlchemyError as e:
            error_msg = f"SQLAlchemyエラーによりメッセージ取得に失敗: channel_id={channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise MessageQueryError(error_msg, e)

        except Exception as e:
            error_msg = f"予期しないエラーによりメッセージ取得に失敗: channel_id={channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise MessageQueryError(error_msg, e)
