from abc import ABC, abstractmethod

from injector import inject, singleton
from repository.channel_repository import ChannelRepositoryIf
from repository.message_repository import MessageRepositoryIf
from schema.channel_schema import ChannelGetResponse
from schema.message_schema import MessageResponse


class ChannelUseCaseIf(ABC):
    """チャネルユースケースのインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @inject
    def __init__(self, channel_repo: ChannelRepositoryIf, message_repo: MessageRepositoryIf) -> None:
        """コンストラクタ

        Args:
            channel_repo: チャネルリポジトリのインターフェース
            message_repo: メッセージリポジトリのインターフェース
        """

        self.channel_repo = channel_repo
        self.message_repo = message_repo

    @abstractmethod
    async def execute(self, session, channel_id: str) -> ChannelGetResponse:
        """チャネル取得処理の実行

        Args:
            session: データベースセッション
            channel_id: チャネルID

        Returns:
            ChannelGetResponse: チャネル情報のレスポンス
        """

        pass


@singleton
class ChannelUseCaseImpl(ChannelUseCaseIf):
    """チャネルユースケースの実装クラス

    Args:
        ChannelUseCaseIf (_type_): チャネルユースケースのインターフェース
    """

    async def execute(self, session, channel_id: str) -> ChannelGetResponse:
        """チャネル情報を取得する

        Args:
            session: データベースセッション
            channel_id: 取得対象のチャネルID

        Returns:
            ChannelGetResponse: チャネル情報（チャネル基本情報 + メッセージ一覧）

        Raises:
            ValueError: 指定されたチャネルが存在しない場合
        """

        # チャネル基本情報を取得
        channel_db = await self.channel_repo.get_channel_by_id(session, channel_id)

        if channel_db is None:
            raise ValueError(f"チャネルが見つかりません: {channel_id}")

        # チャネルに属するメッセージ一覧を取得
        message_list = await self.message_repo.get_message_by_channel_id(session, channel_id)

        # メッセージリストをレスポンス形式に変換
        message_response_data = [MessageResponse.model_validate(message) for message in message_list]

        # チャネル情報のレスポンスデータを構築
        channel_response_data = {
            "id": channel_db.id,
            "guild_id": channel_db.guild_id,
            "name": channel_db.name,
            "messages": message_response_data,
        }

        # レスポンススキーマに変換して返却
        return ChannelGetResponse.model_validate(channel_response_data)
