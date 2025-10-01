from abc import ABC, abstractmethod

from domains import Channel, Friend, GuildMember, User
from injector import inject, singleton
from repository.channel_repository import ChannelRepositoryError, ChannelRepositoryIf
from repository.friend_repository import FriendRepositoryError, FriendRepositoryIf
from repository.guild_member_repository import GuildMemberRepositoryError, GuildMemberRepositoryIf
from repository.guild_repository import GuildRepositoryError, GuildRepositoryIf
from repository.user_repository import UserRepositoryError, UserRepositoryIf
from schema.friend_schema import FriendCreateRequest
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.base_exception import BaseMessageUseCaseError
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


class FriendUseCaseError(BaseMessageUseCaseError):
    """フレンドユースケース例外クラス"""

    pass


class FriendTransactionError(FriendUseCaseError):
    """フレンド作成のトランザクションエラー"""

    pass


class FriendUseCaseIf(ABC):
    """フレンドユースケースインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @inject
    def __init__(
        self,
        user_repo: UserRepositoryIf,
        friend_repo: FriendRepositoryIf,
        guild_repo: GuildRepositoryIf,
        guild_member_repo: GuildMemberRepositoryIf,
        channel_repo: ChannelRepositoryIf,
    ) -> None:
        """フレンドユースケース初期化

        Args:
            user_repo (UserRepositoryIf): ユーザーリポジトリインターフェース
            friend_repo (FriendRepositoryIf): フレンドリポジトリインターフェース
        """

        self.user_repo: UserRepositoryIf = user_repo
        self.friend_repo: FriendRepositoryIf = friend_repo
        self.guild_repo: GuildRepositoryIf = guild_repo
        self.guild_member_repo: GuildMemberRepositoryIf = guild_member_repo
        self.channel_repo: ChannelRepositoryIf = channel_repo

    @abstractmethod
    async def create_friend(self, session: AsyncSession, req: FriendCreateRequest) -> Friend | None:
        """フレンド作成

        Args:
            session (AsyncSession): データベースセッション
            req (FriendCreateRequest): フレンド作成リクエスト

        Returns:
            Friend | None: 作成されたフレンド情報（失敗時はNone）
        """

        pass

    @abstractmethod
    async def get_friend_all(self, session: AsyncSession, user_id: str) -> list[User] | None:
        """すべてのフレンドを取得

        Args:
            session (AsyncSession): データベースセッション
            user_id (str): ユーザーID

        Returns:
            list[User] | None: フレンドのユーザーリスト（失敗時はNone）
        """

        pass


@singleton
class FriendUseCaseImpl(FriendUseCaseIf):
    """フレンドユースケース実装

    Args:
        FriendUseCaseIf (_type_): フレンドユースケースインターフェース
    """

    async def create_friend(self, session: AsyncSession, req: FriendCreateRequest) -> Friend | None:
        """フレンド作成

        Args:
            session (AsyncSession): データベースセッション
            req (FriendCreateRequest): フレンド作成リクエスト

        Returns:
            Friend | None: 作成されたフレンド情報（失敗時はNone）
        """

        try:
            # 自ユーザーの取得
            username = req.username
            user = await self.user_repo.get_user_by_username(session, username)
            if not user:
                return None

            # 相手ユーザーの取得
            related_username = req.related_username
            related_user = await self.user_repo.get_user_by_username(session, related_username)
            if not related_user:
                return None

            friend = Friend(
                user_id=user.id,
                related_user_id=related_user.id,
                type=req.type,
            )

            friend_db = await self.friend_repo.create_friend(session, friend)

            # フレンド追加後、お互いのギルドにフレンドを追加
            guild_db_me = await self.guild_repo.get_guild_by_user_id_name(session, str(friend_db.user_id), "@me")
            guild_member_me = GuildMember(
                user_id=friend_db.related_user_id,
                guild_id=guild_db_me.id,
            )
            _ = await self.guild_member_repo.create_guild_member(session, guild_member_me)

            guild_db_related = await self.guild_repo.get_guild_by_user_id_name(
                session, str(friend_db.related_user_id), "@me"
            )
            guild_member_related = GuildMember(
                user_id=friend_db.user_id,
                guild_id=guild_db_related.id,
            )
            _ = await self.guild_member_repo.create_guild_member(session, guild_member_related)

            # ギルドにフレンドを追加後、それぞれチャネルを作成
            channel_me = Channel(
                guild_id=guild_db_me.id,
                owner_user_id=friend_db.user_id,
            )
            _ = await self.channel_repo.create_channel(session, channel_me)

            channel_related = Channel(
                guild_id=guild_db_related.id,
                owner_user_id=friend_db.related_user_id,
            )
            _ = await self.channel_repo.create_channel(session, channel_related)

        except UserRepositoryError as e:
            raise FriendTransactionError("ユーザー取得中にエラーが発生しました", e)

        except FriendRepositoryError as e:
            raise FriendTransactionError("フレンド作成中にエラーが発生しました", e)

        except GuildRepositoryError as e:
            raise FriendTransactionError("ギルド取得中にエラーが発生しました", e)

        except GuildMemberRepositoryError as e:
            raise FriendTransactionError("ギルドメンバー作成中にエラーが発生しました", e)

        except ChannelRepositoryError as e:
            raise FriendTransactionError("チャンネル作成中にエラーが発生しました", e)

        except Exception as e:
            raise FriendTransactionError("予期しないエラーが発生しました", e)

        return friend_db

    async def get_friend_all(self, session: AsyncSession, user_id: str) -> list[User] | None:
        """すべてのフレンドを取得

        Args:
            session (AsyncSession): データベースセッション
            user_id (str): ユーザーID

        Returns:
            list[User] | None: フレンドのユーザーリスト（失敗時はNone）
        """

        try:
            friends = await self.friend_repo.get_friend_all(session, user_id)

            # 双方向の関係を考慮して相手のユーザーIDを取得
            user_id_list = []
            for friend in friends:
                if str(friend.user_id) == user_id:
                    # 自分がuser_idの場合、related_user_idが相手
                    user_id_list.append(str(friend.related_user_id))
                else:
                    # 自分がrelated_user_idの場合、user_idが相手
                    user_id_list.append(str(friend.user_id))

            return await self.user_repo.get_users_by_id(session, user_id_list)

        except UserRepositoryError as e:
            raise FriendTransactionError("ユーザー取得中にエラーが発生しました", e)

        except FriendRepositoryError as e:
            raise FriendTransactionError("フレンド取得中にエラーが発生しました", e)

        except Exception as e:
            raise FriendTransactionError("予期しないエラーが発生しました", e)
