from abc import ABC, abstractmethod

from fastapi import HTTPException, Request, status
from injector import inject, singleton
from repository.channel_repository import ChannelRepositoryError, ChannelRepositoryIf
from repository.guild_repository import GuildRepositoryError, GuildRepositoryIf
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

logger = get_logger(__name__)


class ChannelAccessCheckerUseCaseIf(ABC):
    """チャンネルアクセス権限チェックユースケースのインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @inject
    def __init__(self, channel_repo: ChannelRepositoryIf, guild_repo: GuildRepositoryIf) -> None:
        """コンストラクタ

        Args:
            channel_repo: チャネルリポジトリのインターフェース
            guild_repo: ギルドリポジトリのインターフェース
        """

        self.channel_repo = channel_repo
        self.guild_repo = guild_repo

    @abstractmethod
    async def execute(self, request: Request, channel_id: str, session: AsyncSession) -> None:
        """チャンネルアクセス権限を検証し、権限がない場合は例外を発生させる

        Args:
            request (Request): HTTPリクエスト（ミドルウェアでユーザー情報が設定済み）
            channel_id (str): チャンネルID
            session (AsyncSession): データベースセッション

        Raises:
            HTTPException: アクセス権限がない場合
        """

        pass


@singleton
class ChannelAccessCheckerUseCaseImpl(ChannelAccessCheckerUseCaseIf):
    """チャンネルアクセス権限チェックユースケースの実装クラス

    Args:
        ChannelAccessCheckerUseCaseIf (_type_): チャンネルアクセス権限チェックユースケースのインターフェース
    """

    async def execute(self, request: Request, channel_id: str, session: AsyncSession) -> None:
        """チャンネルアクセス権限を検証し、権限がない場合は例外を発生させる

        Args:
            request (Request): HTTPリクエスト（ミドルウェアでユーザー情報が設定済み）
            channel_id (str): チャンネルID
            session (AsyncSession): データベースセッション

        Raises:
            HTTPException: アクセス権限がない場合
        """

        # ミドルウェアで設定されたユーザー情報を取得
        user = getattr(request.state, "user", None)
        if not user:
            logger.warning("認証されていないユーザーがチャンネルアクセスを試行")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="認証が必要です")

        ### チャンネルアクセス権限をチェック
        logger.info(f"チャンネルアクセス権限チェック - ユーザーID: {user.id}, チャンネルID: {channel_id}")

        # チャンネルが存在するかチェック
        try:
            channel_db = await self.channel_repo.get_channel_by_id(session, channel_id)

        except ChannelRepositoryError as e:
            logger.error(f"チャンネル情報の取得中にエラーが発生: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サーバーエラーが発生しました"
            )

        except Exception as e:
            # その他の予期しないエラー
            logger.error(f"予期しないエラーが発生: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サーバーエラーが発生しました"
            )

        if not channel_db:
            logger.warning(f"存在しないチャンネルID {channel_id} へのアクセスが試行されました")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定されたチャンネルは存在しません")

        if not bool(channel_db.deleted_at):
            logger.warning(f"ユーザー {user.id} がチャンネル {channel_id} へのアクセスを拒否されました")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="このチャンネルへのアクセス権限がありません"
            )

        # チャンネルが属するギルドのメンバーかどうかをチェック
        try:
            guild_db = await self.guild_repo.get_guild_by_member_channel(session, user.id, channel_id)

        except GuildRepositoryError as e:
            logger.error(f"ギルド情報の取得中にエラーが発生: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サーバーエラーが発生しました"
            )

        except Exception as e:
            # その他の予期しないエラー
            logger.error(f"予期しないエラーが発生: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サーバーエラーが発生しました"
            )

        if not guild_db:
            logger.warning(f"ユーザー {user.id} がチャンネル {channel_id} へのアクセスを拒否されました")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="このチャンネルへのアクセス権限がありません"
            )
