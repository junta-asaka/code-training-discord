from abc import ABC, abstractmethod

from domains import Message
from injector import singleton
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


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
        """

        try:
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"フレンド作成中にDBエラー発生: {e}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"フレンド作成中に予期しないエラー発生: {e}")
            raise
