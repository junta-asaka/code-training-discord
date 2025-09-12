from abc import ABC, abstractmethod

from domains import User
from injector import inject, singleton
from repository.user_repository import UserRepositoryIf
from schema.user_schema import UserCreateRequest
from sqlalchemy.ext.asyncio import AsyncSession
from utils import hash_password


class CreateUserUseCaseIf(ABC):
    """ユーザー作成ユースケースインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @inject
    def __init__(self, repository: UserRepositoryIf) -> None:
        """ユーザー作成ユースケース初期化

        Args:
            repository (UserRepositoryIf): ユーザーリポジトリインターフェース
        """

        self.repository: UserRepositoryIf = repository

    @abstractmethod
    async def execute(self, session: AsyncSession, req: UserCreateRequest) -> User:
        """ユーザー作成ユースケース実行

        Args:
            session (AsyncSession): データベースセッション
            req (UserCreateRequest): ユーザー作成リクエスト

        Returns:
            User: 作成されたユーザー情報
        """

        pass


@singleton
class CreateUserUseCaseImpl(CreateUserUseCaseIf):
    """ユーザー作成ユースケース実装

    Args:
        CreateUserUseCaseIf (_type_): ユーザー作成ユースケースインターフェース
    """

    async def execute(self, session: AsyncSession, req: UserCreateRequest) -> User:
        """ユーザー作成ユースケース実行

        Args:
            session (AsyncSession): データベースセッション
            req (UserCreateRequest): ユーザー作成リクエスト

        Returns:
            User: 作成されたユーザー情報
        """

        password_hash = await hash_password(req.password)
        user = User(
            name=req.name,
            username=req.username,
            email=req.email,
            password_hash=password_hash,
            description=req.description,
        )

        return await self.repository.create_user(session, user)
