from abc import ABC, abstractmethod

from domains import Message
from injector import inject, singleton
from repository.channel_repository import ChannelRepositoryIf
from repository.message_repository import MessageRepositoryIf
from schema.message_schema import MessageCreateRequest, MessageResponse
from sqlalchemy.ext.asyncio import AsyncSession


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
            Message: 作成されたメッセージ
        """

        # メッセージエンティティを作成
        message = Message(
            channel_id=req.channel_id,
            user_id=req.user_id,
            type=req.type,
            content=req.content,
            referenced_message_id=req.referenced_message_id,
        )

        # メッセージをデータベースに保存
        message_db = await self.message_repo.create_message(session, message)

        # チャネルの最終メッセージIDを更新
        await self.channel_repo.update_last_message_id(session, str(message_db.channel_id), str(message_db.id))

        return MessageResponse.model_validate(message_db)
