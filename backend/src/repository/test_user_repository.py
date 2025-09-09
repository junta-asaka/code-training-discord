import os
import unittest
from unittest.mock import AsyncMock
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker
from domains import User
from repository.user_repository import UserRepository
from sqlalchemy.ext.asyncio import create_async_engine


class TestUserRepository(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv()
        DATABASE_URL = os.environ["DATABASE_URL"]
        cls.engine = create_async_engine(DATABASE_URL, echo=True, future=True)
        cls.AsyncSessionLocal = async_sessionmaker(
            bind=cls.engine,
            expire_on_commit=False,
            autoflush=False,
        )

    def setUp(self):
        self.repository = UserRepository()

    async def asyncSetUp(self):
        # テーブル作成
        from domains import Base
        async with self.engine.begin() as conn:
            # SQLiteではFOREIGN KEY制約を無効化（循環参照を回避）
            await conn.execute(text("PRAGMA foreign_keys=OFF"))
            await conn.run_sync(Base.metadata.create_all)
        
        # テーブルクリーンアップ処理を実行（SQLite用）
        async with self.engine.begin() as conn:
            await conn.execute(text("DELETE FROM users"))
            # SQLiteのautoincrement IDをリセット（テーブルが存在する場合のみ）
            try:
                await conn.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'users'"))
            except Exception:
                pass  # sqlite_sequenceテーブルが存在しない場合は無視

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

        # Given
        user_data = User(
            name="Test User",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            description="Test description",
        )
        async with self.AsyncSessionLocal() as session:
            _ = await self.repository.create_user(session, user_data)

        # When / Then
        with self.assertRaises(Exception):
            async with self.AsyncSessionLocal() as session:
                _ = await self.repository.create_user(session, user_data)

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
            result = await self.repository.get_user(
                session, "testuser", "test@example.com", "hashed_password"
            )

        # Then
        result_user: User = result.first()
        self.assertEqual(result_user.name, expected_user.name)  # type: ignore
        self.assertEqual(result_user.username, expected_user.username)  # type: ignore
        self.assertEqual(result_user.email, expected_user.email)  # type: ignore
        self.assertEqual(result_user.password_hash, expected_user.password_hash)  # type: ignore
        self.assertEqual(result_user.description, expected_user.description)  # type: ignore

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
            result = await self.repository.get_user(
                session, "nonexist", "nonexist@example.com", "hashed_password"
            )

        # Then
        self.assertIsNone(result.first())


if __name__ == "__main__":
    unittest.main()
