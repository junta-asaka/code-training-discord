from abc import ABC, abstractmethod
from typing import Optional

from domains import Channel, Guild, GuildMember
from injector import singleton
from sqlalchemy import and_, select, update
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


class ChannelRepositoryError(Exception):
    """チャンネルリポジトリ基底例外クラス"""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class ChannelCreateError(ChannelRepositoryError):
    """チャンネル作成時のエラー"""

    pass


class ChannelDatabaseConstraintError(ChannelRepositoryError):
    """データベース制約違反エラー（外部キー制約など）"""

    pass


class ChannelDatabaseConnectionError(ChannelRepositoryError):
    """データベース接続エラー"""

    pass


class ChannelNotFoundError(ChannelRepositoryError):
    """チャンネルが見つからない場合のエラー"""

    pass


class ChannelQueryError(ChannelRepositoryError):
    """チャンネルクエリ実行時のエラー"""

    pass


class ChannelUpdateError(ChannelRepositoryError):
    """チャンネル更新時のエラー"""

    pass


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
            ChannelDatabaseConstraintError: データベース制約違反の場合
            ChannelDatabaseConnectionError: データベース接続エラーの場合
            ChannelCreateError: チャンネル作成に失敗した場合
        """
        pass

    @abstractmethod
    async def get_channels_by_user_ids_type_name(
        self,
        session: AsyncSession,
        user_ids: list[str],
        type: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Channel:
        """指定したユーザーIDを含むギルドのチャネルを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_ids (list[str]): ユーザーIDのリスト
            type (Optional[str]): チャネルタイプ
            name (Optional[str]): チャネル名

        Returns:
            Channel: チャネル

        Raises:
            ChannelDatabaseConnectionError: データベース接続エラーの場合
            ChannelQueryError: クエリ実行に失敗した場合
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

        Raises:
            ChannelDatabaseConnectionError: データベース接続エラーの場合
            ChannelQueryError: クエリ実行に失敗した場合
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
            ChannelNotFoundError: 指定されたチャンネルが存在しない場合
            ChannelDatabaseConnectionError: データベース接続エラーの場合
            ChannelUpdateError: チャンネル更新に失敗した場合
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
            ChannelDatabaseConstraintError: データベース制約違反の場合
            ChannelDatabaseConnectionError: データベース接続エラーの場合
            ChannelCreateError: チャンネル作成に失敗した場合
        """
        try:
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            logger.info(f"チャンネルが正常に作成されました: channel_id={channel.id}, guild_id={channel.guild_id}")

            return channel

        except IntegrityError as e:
            await session.rollback()
            error_msg = f"データベース制約違反によりチャンネル作成に失敗: guild_id={channel.guild_id}, name={channel.name}, owner_user_id={channel.owner_user_id}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelDatabaseConstraintError(error_msg, e)

        except OperationalError as e:
            await session.rollback()
            error_msg = f"データベース接続エラーによりチャンネル作成に失敗: guild_id={channel.guild_id}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelDatabaseConnectionError(error_msg, e)

        except SQLAlchemyError as e:
            await session.rollback()
            error_msg = f"SQLAlchemyエラーによりチャンネル作成に失敗: guild_id={channel.guild_id}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelCreateError(error_msg, e)

        except Exception as e:
            await session.rollback()
            error_msg = f"予期しないエラーによりチャンネル作成に失敗: guild_id={channel.guild_id}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelCreateError(error_msg, e)

    async def get_channels_by_user_ids_type_name(
        self,
        session: AsyncSession,
        user_ids: list[str],
        type: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Channel:
        """指定したユーザーIDを含むギルドのチャネルを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_ids (list[str]): ユーザーIDのリスト
            type (Optional[str]): チャネルタイプ
            name (Optional[str]): チャネル名

        Returns:
            Channel: チャネル

        Raises:
            ChannelDatabaseConnectionError: データベース接続エラーの場合
            ChannelQueryError: クエリ実行に失敗した場合
        """
        try:
            # 基本的なJOIN条件を構築
            query = (
                select(Channel)
                .join(Guild, Channel.guild_id == Guild.id)
                .join(GuildMember, Guild.id == GuildMember.guild_id)
                .where(GuildMember.user_id.in_(user_ids))
            )

            # 追加の条件を動的に構築
            conditions = []
            if type is not None:
                conditions.append(Channel.type == type)
            if name is not None:
                conditions.append(Channel.name == name)

            # 条件がある場合は追加
            if conditions:
                query = query.where(and_(*conditions))

            # 重複を除去
            query = query.distinct()

            result = await session.execute(query)
            channel = result.scalars().first()

            if channel:
                logger.info(f"ユーザーIDリスト {user_ids} に対応するチャンネルを取得しました: channel_id={channel.id}")
            else:
                logger.info(f"ユーザーIDリスト {user_ids} に対応するチャンネルが見つかりませんでした")

            return channel

        except OperationalError as e:
            error_msg = f"データベース接続エラーによりチャンネル取得に失敗: user_ids={user_ids}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelDatabaseConnectionError(error_msg, e)

        except SQLAlchemyError as e:
            error_msg = f"SQLAlchemyエラーによりチャンネル取得に失敗: user_ids={user_ids}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelQueryError(error_msg, e)

        except Exception as e:
            error_msg = f"予期しないエラーによりチャンネル取得に失敗: user_ids={user_ids}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelQueryError(error_msg, e)

    async def get_channel_by_id(self, session: AsyncSession, channel_id: str) -> Optional[Channel]:
        """チャネルIDからチャネルを取得する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャネルID

        Returns:
            Optional[Channel]: チャネル（存在しない場合はNone）

        Raises:
            ChannelDatabaseConnectionError: データベース接続エラーの場合
            ChannelQueryError: クエリ実行に失敗した場合
        """
        try:
            result = await session.execute(select(Channel).where(Channel.id == channel_id))
            channel = result.scalars().first()

            if channel:
                logger.info(f"チャンネルが見つかりました: channel_id={channel_id}")
            else:
                logger.info(f"チャンネルが見つかりませんでした: channel_id={channel_id}")

            return channel

        except OperationalError as e:
            error_msg = f"データベース接続エラーによりチャンネル取得に失敗: channel_id={channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelDatabaseConnectionError(error_msg, e)

        except SQLAlchemyError as e:
            error_msg = f"SQLAlchemyエラーによりチャンネル取得に失敗: channel_id={channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelQueryError(error_msg, e)

        except Exception as e:
            error_msg = f"予期しないエラーによりチャンネル取得に失敗: channel_id={channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelQueryError(error_msg, e)

    async def update_last_message_id(self, session: AsyncSession, channel_id: str, last_message_id: str) -> None:
        """チャネルのlast_message_idを更新する

        Args:
            session (AsyncSession): データベースセッション
            channel_id (str): チャネルID
            last_message_id (str): 更新するlast_message_id

        Raises:
            ChannelNotFoundError: 指定されたチャンネルが存在しない場合
            ChannelDatabaseConnectionError: データベース接続エラーの場合
            ChannelUpdateError: チャンネル更新に失敗した場合
        """
        try:
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

        except ChannelNotFoundError:
            raise

        except IntegrityError as e:
            error_msg = f"データベース制約違反によりチャンネル更新に失敗: channel_id={channel_id}, last_message_id={last_message_id}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelUpdateError(error_msg, e)

        except OperationalError as e:
            error_msg = f"データベース接続エラーによりチャンネル更新に失敗: channel_id={channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelDatabaseConnectionError(error_msg, e)

        except SQLAlchemyError as e:
            error_msg = f"SQLAlchemyエラーによりチャンネル更新に失敗: channel_id={channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelUpdateError(error_msg, e)

        except Exception as e:
            error_msg = f"予期しないエラーによりチャンネル更新に失敗: channel_id={channel_id}"
            logger.error(f"{error_msg}: {e}")
            raise ChannelUpdateError(error_msg, e)
