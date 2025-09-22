import os
import sys
import unittest
from unittest.mock import AsyncMock

from dotenv import load_dotenv
from injector import Injector
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# テストファイルのルートディレクトリからの相対パスでsrcフォルダを指定
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from dependencies import configure
from domains import Base, User
from repository.user_repository import UserRepositoryIf


class TestUserRepository(unittest.IsolatedAsyncioTestCase):
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
            await conn.execute(text("DELETE FROM messages"))
            await conn.execute(text("DELETE FROM channels"))
            await conn.execute(text("DELETE FROM guild_members"))
            await conn.execute(text("DELETE FROM guilds"))
            await conn.execute(text("DELETE FROM friends"))
            await conn.execute(text("DELETE FROM sessions"))
            await conn.execute(text("DELETE FROM users"))

        # テスト用DIコンテナからユースケースを取得
        injector = Injector([configure])
        self.repository = injector.get(UserRepositoryIf)

    async def asyncTearDown(self):
        # エンジンを非同期に破棄
        await self.engine.dispose()

    async def test_create_user_success(self):
        """
        Given: 有効なユーザー作成リクエスト
        When: create_userメソッドを呼び出す
        Then: ユーザーが正常に作成されること
        """

        # Given
        user_data = User(
            name="Test User",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            description="Test description",
        )

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.create_user(session, user_data)

        # Then
        self.assertEqual(result.name, user_data.name)
        self.assertEqual(result.username, user_data.username)
        self.assertEqual(result.email, user_data.email)
        self.assertEqual(result.password_hash, user_data.password_hash)
        self.assertEqual(result.description, user_data.description)

    async def test_create_user_duplicate(self):
        """
        Given: 重複するユーザー情報
        When: create_userメソッドを呼び出す
        Then: 例外が発生すること
        """

        # Given - 1回目のユーザー作成
        user_data1 = User(
            name="Test User",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            description="Test description",
        )

        async with self.AsyncSessionLocal() as session:
            _ = await self.repository.create_user(session, user_data1)

        # When / Then - 2回目のユーザー作成（重複）
        # 重要: 新しいUserオブジェクトインスタンスを作成
        user_data2 = User(
            name="Test User",
            username="testuser",  # 同じusername（重複）
            email="test@example.com",  # 同じemail（重複）
            password_hash="hashed_password",
            description="Test description",
        )

        with self.assertRaises(SQLAlchemyError):
            async with self.AsyncSessionLocal() as session:
                _ = await self.repository.create_user(session, user_data2)

    async def test_get_user_found(self):
        """
        Given: 既存のユーザー情報が登録済み
        When: get_userメソッドで正しい認証情報を指定
        Then: 該当するユーザーが返されること
        """

        # Given
        expected_user = User(
            name="Test User",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            description="Test description",
        )

        async with self.AsyncSessionLocal() as session:
            _ = await self.repository.create_user(session, expected_user)

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_user_by_username(session, "testuser")

        # Then
        self.assertEqual(result.name, expected_user.name)  # type: ignore
        self.assertEqual(result.username, expected_user.username)  # type: ignore
        self.assertEqual(result.email, expected_user.email)  # type: ignore
        self.assertEqual(result.password_hash, expected_user.password_hash)  # type: ignore
        self.assertEqual(result.description, expected_user.description)  # type: ignore

    async def test_get_user_not_found(self):
        """
        Given: 存在しないユーザーの認証情報
        When: get_userメソッドで不正な認証情報を指定
        Then: Noneが返されること
        """

        # Given
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_user_by_username(session, "nonexist")

        # Then
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
