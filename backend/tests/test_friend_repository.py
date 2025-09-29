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
from domains import Base, Friend, User
from repository.friend_repository import FriendRepositoryIf


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
        with self.assertRaises(Exception):
            async with self.AsyncSessionLocal() as session:
                await self.repository.create_friend(session, friend_data)

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
        with self.assertRaises(Exception):
            async with self.AsyncSessionLocal() as session:
                await self.repository.create_friend(session, friend_data)

    async def test_get_friend_all_success_with_friends(self):
        """
        Given: ユーザーが複数のフレンドを持っている状態
        When: get_friend_allメソッドを呼び出す
        Then: 該当するすべてのフレンドが返されること
        """

        # Given
        friend1 = Friend(
            user_id=self.user1_id,
            related_user_id=self.user2_id,
            type="friend",
        )
        friend2 = Friend(
            user_id=self.user1_id,
            related_user_id=self.user3_id,
            type="friend",
        )

        async with self.AsyncSessionLocal() as session:
            await self.repository.create_friend(session, friend1)
            await self.repository.create_friend(session, friend2)

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_friend_all(session, str(self.user1_id))

        # Then
        self.assertEqual(len(result), 2)
        user_ids = [friend.related_user_id for friend in result]
        self.assertIn(self.user2_id, user_ids)
        self.assertIn(self.user3_id, user_ids)
        for friend in result:
            self.assertEqual(friend.user_id, self.user1_id)
            self.assertEqual(friend.type, "friend")

    async def test_get_friend_all_success_empty_list(self):
        """
        Given: ユーザーがフレンドを持っていない状態
        When: get_friend_allメソッドを呼び出す
        Then: 空のリストが返されること
        """

        # Given
        # フレンドが存在しない状態（セットアップで既にクリーンアップ済み）

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_friend_all(session, str(self.user1_id))

        # Then
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    async def test_get_friend_all_success_nonexistent_user(self):
        """
        Given: 存在しないuser_idを指定
        When: get_friend_allメソッドを呼び出す
        Then: 空のリストが返されること
        """

        # Given
        nonexistent_user_id = str(uuid.uuid4())

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_friend_all(session, nonexistent_user_id)

        # Then
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    async def test_get_friend_all_success_specific_user_only(self):
        """
        Given: 複数のユーザーがそれぞれフレンドを持っている状態
        When: 特定のユーザーでget_friend_allメソッドを呼び出す
        Then: そのユーザーのフレンドのみが返されること
        """

        # Given
        # user1のフレンド
        friend1 = Friend(
            user_id=self.user1_id,
            related_user_id=self.user2_id,
            type="friend",
        )
        # user2のフレンド
        friend2 = Friend(
            user_id=self.user2_id,
            related_user_id=self.user3_id,
            type="friend",
        )

        async with self.AsyncSessionLocal() as session:
            await self.repository.create_friend(session, friend1)
            await self.repository.create_friend(session, friend2)

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_friend_all(session, str(self.user1_id))

        # Then
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].user_id, self.user1_id)
        self.assertEqual(result[0].related_user_id, self.user2_id)
        self.assertEqual(result[0].type, "friend")

    async def test_get_friend_all_success_different_friend_types(self):
        """
        Given: ユーザーが異なるタイプのフレンドを持っている状態
        When: get_friend_allメソッドを呼び出す
        Then: タイプに関係なくすべてのフレンドが返されること
        """

        # Given
        friend1 = Friend(
            user_id=self.user1_id,
            related_user_id=self.user2_id,
            type="friend",
        )
        friend2 = Friend(
            user_id=self.user1_id,
            related_user_id=self.user3_id,
            type="blocked",
        )

        async with self.AsyncSessionLocal() as session:
            await self.repository.create_friend(session, friend1)
            await self.repository.create_friend(session, friend2)

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_friend_all(session, str(self.user1_id))

        # Then
        self.assertEqual(len(result), 2)
        types = [friend.type for friend in result]
        self.assertIn("friend", types)
        self.assertIn("blocked", types)


if __name__ == "__main__":
    unittest.main()
