import os
import sys
import unittest
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from injector import Injector
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# テストファイルのルートディレクトリからの相対パスでsrcフォルダを指定
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from dependencies import configure
from domains import Base, Session, User
from repository.session_repository import SessionRepositoryIf


class TestSessionRepository(unittest.IsolatedAsyncioTestCase):
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
        self.repository = injector.get(SessionRepositoryIf)

        # テスト用ユーザーを作成（セッション作成時に必要な外部キー）
        self.test_user = User(
            name="Test User",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            description="Test description",
        )

        async with self.AsyncSessionLocal() as session:
            session.add(self.test_user)
            await session.commit()
            await session.refresh(self.test_user)

    async def asyncTearDown(self):
        # エンジンを非同期に破棄
        await self.engine.dispose()

    async def test_create_session_success(self):
        """
        Given: 有効なセッション作成リクエスト
        When: create_sessionメソッドを呼び出す
        Then: セッションが正常に作成されること
        """

        # Given
        session_data = Session(
            user_id=self.test_user.id,
            refresh_token_hash="refresh_token_hash",
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.1",
            revoked_at=None,
        )

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.create_session(session, session_data)

        # Then
        self.assertEqual(result.user_id, session_data.user_id)
        self.assertEqual(result.refresh_token_hash, session_data.refresh_token_hash)
        self.assertEqual(result.user_agent, session_data.user_agent)
        self.assertEqual(result.ip_address, session_data.ip_address)
        self.assertEqual(result.revoked_at, session_data.revoked_at)
        self.assertIsNotNone(result.id)
        self.assertIsNotNone(result.created_at)

    async def test_create_session_with_revoked_at(self):
        """
        Given: revoked_atが設定されたセッション作成リクエスト
        When: create_sessionメソッドを呼び出す
        Then: セッションが正常に作成されること
        """

        # Given
        revoked_time = datetime.now(timezone.utc)
        session_data = Session(
            user_id=self.test_user.id,
            refresh_token_hash="refresh_token_hash_with_revoked",
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.1",
            revoked_at=revoked_time,
        )

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.create_session(session, session_data)

        # Then
        self.assertEqual(result.user_id, session_data.user_id)
        self.assertEqual(result.refresh_token_hash, session_data.refresh_token_hash)
        self.assertEqual(result.user_agent, session_data.user_agent)
        self.assertEqual(result.ip_address, session_data.ip_address)
        self.assertEqual(result.revoked_at, revoked_time)

    async def test_create_session_duplicate_refresh_token(self):
        """
        Given: 既に存在するrefresh_token_hashでのセッション作成
        When: create_sessionメソッドを呼び出す
        Then: 例外が発生すること
        """

        # Given - 1回目のセッション作成
        session_data1 = Session(
            user_id=self.test_user.id,
            refresh_token_hash="refresh_token_hash_duplicate",
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.1",
            revoked_at=None,
        )

        # 最初のセッション作成
        async with self.AsyncSessionLocal() as session:
            _ = await self.repository.create_session(session, session_data1)

        # When / Then - 2回目のセッション作成（重複）
        # 重要: 新しいSessionオブジェクトインスタンスを作成
        session_data2 = Session(
            user_id=self.test_user.id,
            refresh_token_hash="refresh_token_hash_duplicate",  # 同じrefresh_token_hash（重複）
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.1",
            revoked_at=None,
        )

        with self.assertRaises(SQLAlchemyError):
            async with self.AsyncSessionLocal() as session:
                _ = await self.repository.create_session(session, session_data2)

    async def test_get_session_by_token_found(self):
        """
        Given: 既存のセッション情報が登録済み
        When: get_session_by_tokenメソッドで正しいトークンを指定
        Then: 該当するセッションが返されること
        """

        # Given
        expected_session = Session(
            user_id=self.test_user.id,
            refresh_token_hash="refresh_token_hash",
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.1",
            revoked_at=None,
        )

        async with self.AsyncSessionLocal() as session:
            created_session = await self.repository.create_session(session, expected_session)

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_session_by_token(session, "refresh_token_hash")

        # Then
        self.assertIsNotNone(result)
        self.assertEqual(result.id, created_session.id)  # type: ignore
        self.assertEqual(result.user_id, expected_session.user_id)  # type: ignore
        self.assertEqual(result.refresh_token_hash, expected_session.refresh_token_hash)  # type: ignore
        self.assertEqual(result.user_agent, expected_session.user_agent)  # type: ignore
        self.assertEqual(result.ip_address, expected_session.ip_address)  # type: ignore
        self.assertEqual(result.revoked_at, expected_session.revoked_at)  # type: ignore

    async def test_get_session_by_token_not_found(self):
        """
        Given: 存在しないトークン
        When: get_session_by_tokenメソッドで存在しないトークンを指定
        Then: Noneが返されること
        """

        # Given / When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_session_by_token(session, "refresh_token_hash")

        # Then
        self.assertIsNone(result)

    async def test_get_session_by_token_empty_string(self):
        """
        Given: 空文字のトークン
        When: get_session_by_tokenメソッドで空文字を指定
        Then: Noneが返されること
        """

        # Given / When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_session_by_token(session, "")

        # Then
        self.assertIsNone(result)

    async def test_get_session_by_token_multiple_sessions(self):
        """
        Given: 複数のセッションが登録済み
        When: get_session_by_tokenメソッドで特定のトークンを指定
        Then: 該当する正しいセッションが返されること
        """

        # Given - 複数のセッションを作成
        session_data_1 = Session(
            user_id=self.test_user.id,
            refresh_token_hash="refresh_token_hash_1",
            user_agent="Browser 1",
            ip_address="192.168.1.1",
            revoked_at=None,
        )

        session_data_2 = Session(
            user_id=self.test_user.id,
            refresh_token_hash="refresh_token_hash_2",
            user_agent="Browser 2",
            ip_address="192.168.1.2",
            revoked_at=None,
        )

        async with self.AsyncSessionLocal() as session:
            _ = await self.repository.create_session(session, session_data_1)

        async with self.AsyncSessionLocal() as session:
            created_session_2 = await self.repository.create_session(session, session_data_2)

        # When
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_session_by_token(session, "refresh_token_hash_2")

        # Then
        self.assertIsNotNone(result)
        self.assertEqual(result.id, created_session_2.id)  # type: ignore
        self.assertEqual(result.refresh_token_hash, "refresh_token_hash_2")  # type: ignore
        self.assertEqual(result.user_agent, "Browser 2")  # type: ignore
        self.assertEqual(result.ip_address, "192.168.1.2")  # type: ignore

    async def test_create_session_invalid_user_id(self):
        """
        Given: 存在しないuser_idでのセッション作成
        When: create_sessionメソッドを呼び出す
        Then: 例外が発生すること
        """

        # Given
        invalid_user_id = uuid.uuid4()  # 存在しないユーザーID
        session_data = Session(
            user_id=invalid_user_id,
            refresh_token_hash="refresh_token_hash",
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.1",
            revoked_at=None,
        )

        # When / Then
        with self.assertRaises(Exception):  # 外部キー制約違反
            async with self.AsyncSessionLocal() as session:
                _ = await self.repository.create_session(session, session_data)


if __name__ == "__main__":
    unittest.main()
