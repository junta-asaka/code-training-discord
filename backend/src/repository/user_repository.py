from abc import ABC, abstractmethod

from domains import User
from injector import singleton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepositoryIf(ABC):
    """ユーザーリポジトリインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @abstractmethod
    async def create_user(self, session: AsyncSession, user: User) -> User:
        """ユーザーを作成する

        Args:
            session (AsyncSession): データベースセッション
            user (User): 作成するユーザー情報

        Returns:
            User: 作成されたユーザー情報
        """

        pass

    @abstractmethod
    async def get_user_by_username(self, session: AsyncSession, username: str) -> User:
        """ユーザーを取得する

        Args:
            session (AsyncSession): データベースセッション
            username (str): ユーザー名
        """

        pass

    @abstractmethod
    async def get_users_by_id(self, session: AsyncSession, user_id_list: list[str]) -> list[User]:
        """複数のユーザーを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_id_list (list[str]): ユーザーIDリスト

        Returns:
            list[User]: ユーザーリスト
        """

        pass


@singleton
class UserRepositoryImpl(UserRepositoryIf):
    """ユーザーリポジトリ実装

    Args:
        UserRepositoryIf (_type_): ユーザーリポジトリインターフェース
    """

    async def create_user(self, session: AsyncSession, user: User) -> User:
        """ユーザーを作成する

        Args:
            session (AsyncSession): データベースセッション
            user (User): 作成するユーザー情報

        Returns:
            User: 作成されたユーザー情報
        """

        user_db = User(
            name=user.name,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            description=user.description,
        )

        session.add(user_db)
        await session.commit()
        await session.refresh(user_db)

        return user_db

    async def get_user_by_username(self, session: AsyncSession, username: str) -> User:
        """ユーザーを取得する

        Args:
            session (AsyncSession): データベースセッション
            username (str): ユーザー名
        """

        stmt = select(User).where(
            User.username == username,
        )
        result = await session.execute(stmt)

        return result.scalars().first()

    async def get_users_by_id(self, session: AsyncSession, user_id_list: list[str]) -> list[User]:
        """複数のユーザーを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_id_list (list[str]): ユーザーIDリスト

        Returns:
            list[User]: ユーザーリスト
        """

        stmt = select(User).where(
            User.id.in_(user_id_list),
        )
        result = await session.execute(stmt)

        return list(result.scalars().all())
