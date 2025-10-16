import os
import sys
import unittest
import uuid

from dotenv import load_dotenv
from injector import Injector
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# テストファイルのルートディレクトリからの相対パスでsrcフォルダを指定
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from dependencies import configure
from domains import Base, Channel, Friend, Guild, User
from repository.friend_repository import FriendCreateError, FriendRepositoryIf


class TestFriendRepository(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv()
        DATABASE_URL = os.environ["DATABASE_URL_TEST"]
        cls.engine = create_async_engine(DATABASE_URL, echo=True, future=True)
        cls.AsyncSessionLocal = async_sessionmaker(
            bind=cls.engine,
            expire_on_commit=False,
            autoflush=False,
        )

    async def asyncSetUp(self):
        # テーブル作成
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # テーブルクリーンアップ処理を実行
        async with self.engine.begin() as conn:
            # 外部キー制約のため、子テーブルから削除
            await conn.execute(text("DELETE FROM channels"))
            await conn.execute(text("DELETE FROM messages"))
            await conn.execute(text("DELETE FROM guild_members"))
            await conn.execute(text("DELETE FROM guilds"))
            await conn.execute(text("DELETE FROM friends"))
            await conn.execute(text("DELETE FROM sessions"))
            await conn.execute(text("DELETE FROM users"))

        # テスト用DIコンテナからリポジトリを取得
        injector = Injector([configure])
        self.repository = injector.get(FriendRepositoryIf)

        # テスト用ユーザーを作成
        self.user1_id = uuid.uuid4()
        self.user2_id = uuid.uuid4()
        self.user3_id = uuid.uuid4()

        async with self.AsyncSessionLocal() as session:
            # テスト用ユーザー1を作成
            user1 = User(
                id=self.user1_id,
                name="Test User 1",
                username="testuser1",
                email="test1@example.com",
                password_hash="hashed_password1",
                description="Test description 1",
            )
            # テスト用ユーザー2を作成
            user2 = User(
                id=self.user2_id,
                name="Test User 2",
                username="testuser2",
                email="test2@example.com",
                password_hash="hashed_password2",
                description="Test description 2",
            )
            # テスト用ユーザー3を作成
            user3 = User(
                id=self.user3_id,
                name="Test User 3",
                username="testuser3",
                email="test3@example.com",
                password_hash="hashed_password3",
                description="Test description 3",
            )

            session.add_all([user1, user2, user3])
            await session.commit()

    async def asyncTearDown(self):
        # エンジンを非同期に破棄
        await self.engine.dispose()

    async def create_test_guild(self, user_id: uuid.UUID, name: str = "@me") -> Guild:
        """テスト用ギルドを作成"""
        guild = Guild(
            name=name,
            owner_user_id=user_id,
        )
        async with self.AsyncSessionLocal() as session:
            session.add(guild)
            await session.commit()
            await session.refresh(guild)
            return guild

    async def create_test_channel(
        self, guild_id, related_guild_id, owner_user_id: uuid.UUID
    ) -> Channel:
        """テスト用チャンネルを作成"""
        channel = Channel(
            type="text",
            name="",
            guild_id=guild_id,
            related_guild_id=related_guild_id,
            owner_user_id=owner_user_id,
        )
        async with self.AsyncSessionLocal() as session:
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            return channel

    async def test_create_friend_success(self):
        """
        Given: 有効なフレンド作成リクエスト
        When: create_friendメソッドを呼び出す
        Then: フレンドが正常に作成されること
        """

        # Given
        friend_data = Friend(
            user_id=self.user1_id,
            related_user_id=self.user2_id,
            type="friend",
        )

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.create_friend(session, friend_data)

        # Then
        self.assertEqual(result.user_id, friend_data.user_id)
        self.assertEqual(result.related_user_id, friend_data.related_user_id)
        self.assertEqual(result.type, friend_data.type)
        self.assertIsNotNone(result.id)
        self.assertIsNotNone(result.created_at)

    async def test_create_friend_duplicate(self):
        """
        Given: 既に存在するフレンド関係
        When: 同じuser_idとrelated_user_idでcreate_friendメソッドを呼び出す
        Then: 例外が発生すること
        """

        # Given
        friend_data = Friend(
            user_id=self.user1_id,
            related_user_id=self.user2_id,
            type="friend",
        )
        async with self.AsyncSessionLocal() as session:
            await self.repository.create_friend(session, friend_data)
            await session.commit()  # テスト用に明示的にcommit

        # When / Then
        duplicate_friend_data = Friend(
            user_id=self.user1_id,
            related_user_id=self.user2_id,
            type="friend",
        )
        with self.assertRaises(Exception):
            async with self.AsyncSessionLocal() as session:
                await self.repository.create_friend(session, duplicate_friend_data)

    async def test_create_friend_nonexistent_user_id(self):
        """
        Given: 存在しないuser_idを指定したフレンド作成リクエスト
        When: create_friendメソッドを呼び出す
        Then: 外部キー制約エラーが発生すること
        """

        # Given
        nonexistent_user_id = uuid.uuid4()
        friend_data = Friend(
            user_id=nonexistent_user_id,
            related_user_id=self.user2_id,
            type="friend",
        )

        # When / Then
        with self.assertRaises(FriendCreateError) as context:
            async with self.AsyncSessionLocal() as session:
                await self.repository.create_friend(session, friend_data)

        # エラーメッセージに適切な情報が含まれていることを確認
        error_message = str(context.exception)
        self.assertIn("データベース制約違反", error_message)

        # 元の例外が保持されていることを確認
        self.assertIsNotNone(context.exception.original_error)

    async def test_create_friend_nonexistent_related_user_id(self):
        """
        Given: 存在しないrelated_user_idを指定したフレンド作成リクエスト
        When: create_friendメソッドを呼び出す
        Then: 外部キー制約エラーが発生すること
        """

        # Given
        nonexistent_user_id = uuid.uuid4()
        friend_data = Friend(
            user_id=self.user1_id,
            related_user_id=nonexistent_user_id,
            type="friend",
        )

        # When / Then
        with self.assertRaises(FriendCreateError) as context:
            async with self.AsyncSessionLocal() as session:
                await self.repository.create_friend(session, friend_data)

        # エラーメッセージに適切な情報が含まれていることを確認
        error_message = str(context.exception)
        self.assertIn("データベース制約違反", error_message)

        # 元の例外が保持されていることを確認
        self.assertIsNotNone(context.exception.original_error)

    async def test_get_friends_with_details_multiple_friends(self):
        """
        Given: 複数のフレンド関係が存在する場合
        When: get_friends_with_detailsメソッドを呼び出す
        Then: すべてのフレンドの詳細情報が取得されること
        """

        # Given
        friend1_data = Friend(
            user_id=self.user1_id,
            related_user_id=self.user2_id,
            type="friend",
        )
        friend2_data = Friend(
            user_id=self.user1_id,
            related_user_id=self.user3_id,
            type="friend",
        )
        async with self.AsyncSessionLocal() as session:
            await self.repository.create_friend(session, friend1_data)
            await self.repository.create_friend(session, friend2_data)
            await session.commit()

        # ギルドとチャンネルを作成
        guild1 = await self.create_test_guild(self.user1_id, "@me")
        guild2 = await self.create_test_guild(self.user2_id, "@me")
        guild3 = await self.create_test_guild(self.user3_id, "@me")

        await self.create_test_channel(guild1.id, guild2.id, self.user1_id)
        await self.create_test_channel(guild1.id, guild3.id, self.user1_id)

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_friends_with_details(
                session, str(self.user1_id)
            )

        # Then
        self.assertEqual(len(result), 2)
        usernames = [row.user_username for row in result]
        self.assertIn("testuser2", usernames)
        self.assertIn("testuser3", usernames)

    async def test_get_friends_with_details_bidirectional_friendship(self):
        """
        Given: 双方向のフレンド関係が存在する場合
        When: 両方のユーザーでget_friends_with_detailsメソッドを呼び出す
        Then: 相互にフレンド情報が取得されること
        """

        # Given
        friend_data = Friend(
            user_id=self.user1_id,
            related_user_id=self.user2_id,
            type="friend",
        )

        async with self.AsyncSessionLocal() as session:
            await self.repository.create_friend(session, friend_data)
            await session.commit()

        # ギルドとチャンネルを作成
        guild1 = await self.create_test_guild(self.user1_id, "@me")
        guild2 = await self.create_test_guild(self.user2_id, "@me")
        await self.create_test_channel(guild1.id, guild2.id, self.user1_id)

        # When
        async with self.AsyncSessionLocal() as session:
            result1 = await self.repository.get_friends_with_details(
                session, str(self.user1_id)
            )
            result2 = await self.repository.get_friends_with_details(
                session, str(self.user2_id)
            )

        # Then
        self.assertEqual(len(result1), 1)
        self.assertEqual(result1[0].user_username, "testuser2")

        self.assertEqual(len(result2), 1)
        self.assertEqual(result2[0].user_username, "testuser1")

    async def test_get_friends_with_details_no_friends(self):
        """
        Given: フレンドが存在しないユーザー
        When: get_friends_with_detailsメソッドを呼び出す
        Then: 空のリストが返されること
        """

        # Given

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_friends_with_details(
                session, str(self.user1_id)
            )

        # Then
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    async def test_get_friends_with_details_nonexistent_user(self):
        """
        Given: 存在しないユーザーID
        When: get_friends_with_detailsメソッドを呼び出す
        Then: 空のリストが返されること
        """

        # Given
        nonexistent_user_id = str(uuid.uuid4())

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_friends_with_details(
                session, nonexistent_user_id
            )

        # Then
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()
