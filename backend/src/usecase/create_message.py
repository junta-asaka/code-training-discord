from abc import ABC, abstractmethod

from domains import Message
from injector import inject, singleton
from repository.channel_repository import (
    ChannelNotFoundError as ChannelRepoNotFoundError,
)
from repository.channel_repository import (
    ChannelRepositoryError,
    ChannelRepositoryIf,
)
from repository.message_repository import (
    MessageRepositoryError,
    MessageRepositoryIf,
)
from schema.message_schema import MessageCreateRequest, MessageResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.base_exception import BaseMessageUseCaseError


class CreateMessageUseCaseError(BaseMessageUseCaseError):
    """メッセージ作成ユースケース例外クラス"""

    pass


class ChannelNotFoundError(CreateMessageUseCaseError):
    """チャンネルが見つからない場合のエラー"""

    pass


class CreateMessageTransactionError(CreateMessageUseCaseError):
    """メッセージ作成のトランザクションエラー"""

    pass


class CreateMessageUseCaseIf(ABC):
    """メッセージ作成ユースケースのインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @inject
    def __init__(self, message_repo: MessageRepositoryIf, channel_repo: ChannelRepositoryIf) -> None:
        """メッセージ作成ユースケース初期化

        Args:
            message_repo (MessageRepositoryIf): メッセージリポジトリのインターフェース
            channel_repo (ChannelRepositoryIf): チャネルリポジトリのインターフェース
        """

        self.message_repo = message_repo
        self.channel_repo = channel_repo

    @abstractmethod
    async def execute(self, session: AsyncSession, req: MessageCreateRequest) -> MessageResponse:
        """メッセージ作成処理の実行

        Args:
            session (AsyncSession): データベースセッション
            req (MessageCreateRequest): メッセージ作成リクエスト

        Returns:
            Message: 作成されたメッセージ
        """

        pass


@singleton
class CreateMessageUseCaseImpl(CreateMessageUseCaseIf):
    """メッセージ作成ユースケースの実装クラス

    Args:
        CreateMessageUseCaseIf (_type_): メッセージ作成ユースケースのインターフェース
    """

    async def execute(self, session: AsyncSession, req: MessageCreateRequest) -> MessageResponse:
        """メッセージを作成し、チャネルの最終メッセージIDを更新する

        Args:
            session (AsyncSession): データベースセッション
            req (MessageCreateRequest): メッセージ作成リクエスト

        Returns:
            MessageResponse: 作成されたメッセージのレスポンス

        Raises:
            ChannelNotFoundError: 指定されたチャンネルが存在しない場合
            MessageTransactionError: メッセージ作成のトランザクションに失敗した場合
        """
        try:
            # メッセージエンティティを作成
            message = Message(
                channel_id=req.channel_id,
                user_id=req.user_id,
                type=req.type,
                content=req.content,
                referenced_message_id=req.referenced_message_id,
            )

            # メッセージをデータベースに保存（flush のみ、commit はまだ行わない）
            message_db = await self.message_repo.create_message(session, message)

            # チャネルの最終メッセージIDを更新（commit はまだ行わない）
            await self.channel_repo.update_last_message_id(session, str(message_db.channel_id), str(message_db.id))

            # 両方の操作が成功した場合に commit
            await session.commit()

            return MessageResponse.model_validate(message_db)

        except ChannelRepoNotFoundError as e:
            await session.rollback()
            raise ChannelNotFoundError(f"指定されたチャンネル（ID: {req.channel_id}）が存在しません", e)

        except MessageRepositoryError as e:
            # リポジトリ層のエラーをユースケース層のエラーに変換
            await session.rollback()
            if isinstance(e.original_error, IntegrityError):
                raise ChannelNotFoundError(f"指定されたチャンネル（ID: {req.channel_id}）が存在しません", e)
            raise CreateMessageTransactionError("メッセージの作成中にエラーが発生しました", e)

        except ChannelRepositoryError as e:
            # チャネルの更新に失敗した場合
            await session.rollback()
            raise CreateMessageTransactionError("チャネルの更新中にエラーが発生しました", e)

        except Exception as e:
            # その他の予期しないエラー
            await session.rollback()
            raise CreateMessageTransactionError("予期しないエラーが発生しました", e)
