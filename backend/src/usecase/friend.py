from abc import ABC, abstractmethod

from domains import Friend, User
from injector import inject, singleton
from repository.friend_repository import FriendRepositoryIf
from repository.user_repository import UserRepositoryIf
from schema.friend_schema import FriendCreateRequest
from sqlalchemy.ext.asyncio import AsyncSession


class FriendUseCaseIf(ABC):
    """フレンドユースケースインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @inject
    def __init__(self, user_repo: UserRepositoryIf, friend_repo: FriendRepositoryIf) -> None:
        """フレンドユースケース初期化

        Args:
            user_repo (UserRepositoryIf): ユーザーリポジトリインターフェース
            friend_repo (FriendRepositoryIf): フレンドリポジトリインターフェース
        """

        self.user_repo: UserRepositoryIf = user_repo
        self.friend_repo: FriendRepositoryIf = friend_repo

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

        return await self.friend_repo.create_friend(session, friend)

    async def get_friend_all(self, session: AsyncSession, user_id: str) -> list[User] | None:
        """すべてのフレンドを取得

        Args:
            session (AsyncSession): データベースセッション
            user_id (str): ユーザーID

        Returns:
            list[User] | None: フレンドのユーザーリスト（失敗時はNone）
        """

        friends = await self.friend_repo.get_friend_all(session, user_id)
        user_id_list = [str(friend.related_user_id) for friend in friends]

        return await self.user_repo.get_users_by_id(session, user_id_list)
