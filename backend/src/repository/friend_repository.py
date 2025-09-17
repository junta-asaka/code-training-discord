from abc import ABC, abstractmethod

from domains import Friend
from injector import singleton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class FriendRepositoryIf(ABC):
    """フレンドリポジトリインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @abstractmethod
    async def create_friend(self, session: AsyncSession, friend: Friend) -> Friend:
        """フレンドを作成する

        Args:
            session (AsyncSession): データベースセッション
            friend (Friend): 作成するフレンド情報

        Returns:
            Friend: 作成されたフレンド情報
        """

        pass

    @abstractmethod
    async def get_friend_all(self, session: AsyncSession, user_id: str) -> list[Friend]:
        """すべてのフレンドを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_id (str): ユーザーID

        Returns:
            list[Friend]: フレンドリスト
        """

        pass


@singleton
class FriendRepositoryImpl(FriendRepositoryIf):
    """フレンドリポジトリ実装

    Args:
        FriendRepositoryIf (_type_): フレンドリポジトリインターフェース
    """

    async def create_friend(self, session: AsyncSession, friend: Friend) -> Friend:
        """フレンドを作成する

        Args:
            session (AsyncSession): データベースセッション
            friend (Friend): 作成するフレンド情報

        Returns:
            Friend: 作成されたフレンド情報
        """

        session.add(friend)
        await session.commit()
        await session.refresh(friend)

        return friend

    async def get_friend_all(self, session: AsyncSession, user_id: str) -> list[Friend]:
        """すべてのフレンドを取得する

        Args:
            session (AsyncSession): データベースセッション
            user_id (str): ユーザーID

        Returns:
            list[Friend]: フレンドリスト
        """

        result = await session.execute(select(Friend).where(Friend.user_id == user_id))

        return list(result.scalars().all())
