from abc import ABC, abstractmethod

from injector import inject, singleton
from repository.channel_repository import (
    ChannelRepositoryError,
    ChannelRepositoryIf,
)
from repository.message_repository import (
    MessageRepositoryError,
    MessageRepositoryIf,
)
from schema.channel_schema import ChannelGetResponse
from schema.message_schema import MessageResponse
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


class GetChannelMessagesUseCaseError(Exception):
    """チャンネルメッセージ取得ユースケース基底例外クラス"""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class ChannelNotFoundError(GetChannelMessagesUseCaseError):
    """チャンネルが見つからない場合のエラー"""

    pass


class GetChannelMessageTransactionError(GetChannelMessagesUseCaseError):
    """チャンネルメッセージ取得時のエラー"""

    pass


class GetChannelMessagesUseCaseIf(ABC):
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

        Raises:
            ChannelNotFoundError: 指定されたチャンネルが存在しない場合
            GetChannelMessageTransactionError: チャンネルメッセージ取得に失敗した場合
        """
        pass


@singleton
class GetChannelMessagesUseCaseImpl(GetChannelMessagesUseCaseIf):
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
            ChannelNotFoundError: 指定されたチャンネルが存在しない場合
            GetChannelMessageTransactionError: チャンネルメッセージ取得に失敗した場合
        """

        # チャネル基本情報を取得
        try:
            channel_db = await self.channel_repo.get_channel_by_id(session, channel_id)
            if channel_db is None:
                error_msg = f"指定されたチャンネルが存在しません: channel_id={channel_id}"
                logger.warning(error_msg)
                raise ChannelNotFoundError(error_msg)
            logger.info(f"チャンネル基本情報を取得しました: channel_id={channel_id}, name={channel_db.name}")

            # チャネルに属するメッセージ一覧を取得
            message_list = await self.message_repo.get_message_by_channel_id(session, channel_id)
            logger.info(f"メッセージ一覧を取得しました: channel_id={channel_id}, message_count={len(message_list)}")

            # データ変換処理
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
            response = ChannelGetResponse.model_validate(channel_response_data)
            logger.info(
                f"チャンネルメッセージ取得が正常に完了: channel_id={channel_id}, message_count={len(message_response_data)}"
            )

            return response

        except ChannelNotFoundError as e:
            raise ChannelNotFoundError(str(e))

        except ChannelRepositoryError as e:
            raise GetChannelMessageTransactionError("チャンネルメッセージ取得中にエラーが発生しました", e)

        except MessageRepositoryError as e:
            raise GetChannelMessageTransactionError("メッセージ取得中にエラーが発生しました", e)

        except Exception as e:
            # その他の予期しないエラー
            raise GetChannelMessageTransactionError("予期しないエラーが発生しました", e)
