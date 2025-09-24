import os
import sys
import unittest
import uuid
from typing import AsyncGenerator

from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# テストファイルのルートディレクトリからの相対パスでsrcフォルダを指定
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from database import get_session
from domains import Base, Channel, Guild, Message, User
from main import app


class TestMessageAPI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # テスト環境であることを示す環境変数を設定
        os.environ["TESTING"] = "true"

        load_dotenv()
        DATABASE_URL = os.environ["DATABASE_URL_TEST"]
        self.engine = create_async_engine(DATABASE_URL, echo=True, future=True)
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
        )

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

        # テスト用のデータベースセッション依存関数をオーバーライド
        async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
            async with self.AsyncSessionLocal() as session:
                yield session

        app.dependency_overrides[get_session] = override_get_session

        # 非同期でAsyncClientを初期化
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")

        # テスト用データを作成
        await self._create_test_data()

    async def _create_test_data(self):
        """テスト用データを作成"""
        async with self.AsyncSessionLocal() as session:
            # テスト用ユーザー作成
            self.test_user_id = uuid.uuid4()
            test_user = User(
                id=self.test_user_id,
                name="Test User",
                username="testuser",
                email="test@example.com",
                password_hash="testpassword",
            )
            session.add(test_user)
            # ユーザーを先にコミットして、外部キー制約を満たす
            await session.commit()

            # テスト用ギルド作成
            self.test_guild_id = uuid.uuid4()
            test_guild = Guild(
                id=self.test_guild_id,
                name="Test Guild",
                owner_user_id=self.test_user_id,
            )
            session.add(test_guild)
            # ギルドをコミット
            await session.commit()

            # テスト用チャネル作成
            self.test_channel_id = uuid.uuid4()
            test_channel = Channel(
                id=self.test_channel_id,
                guild_id=self.test_guild_id,
                type="text",
                name="general",
                owner_user_id=self.test_user_id,
            )
            session.add(test_channel)
            # チャネルをコミット
            await session.commit()

            # 返信元となるメッセージ作成
            self.test_original_message_id = uuid.uuid4()
            test_original_message = Message(
                id=self.test_original_message_id,
                channel_id=self.test_channel_id,
                user_id=self.test_user_id,
                type="default",
                content="Original message for reply test",
            )
            session.add(test_original_message)
            # 最終コミット
            await session.commit()

    async def asyncTearDown(self):
        # テスト環境変数をクリーンアップ
        if "TESTING" in os.environ:
            del os.environ["TESTING"]

        # 依存関数のオーバーライドを削除
        app.dependency_overrides.clear()
        # クライアントを非同期に破棄
        await self.client.aclose()
        # エンジンを非同期に破棄
        await self.engine.dispose()

    async def test_post_message_to_channel_success_normal_message(self):
        """
        Given: 有効なチャネルIDと通常のメッセージデータ
        When: POST /api/channels/{channel_id}/messages にリクエスト
        Then: 201でメッセージ作成成功レスポンスが返る
        """

        # Given: 有効なチャネルIDと通常のメッセージデータ
        channel_id = str(self.test_channel_id)
        message_data = {
            "user_id": str(self.test_user_id),
            "type": "default",
            "content": "Hello, world!",
            "referenced_message_id": None,
        }

        # When: POST /api/channels/{channel_id}/messages にリクエスト
        response = await self.client.post(f"/api/channels/{channel_id}/messages", json=message_data)

        # Then: 201でメッセージ作成成功レスポンスが返る
        self.assertEqual(response.status_code, 201)
        res_json = response.json()

        self.assertEqual(res_json["channel_id"], channel_id)
        self.assertEqual(res_json["user_id"], str(self.test_user_id))
        self.assertEqual(res_json["type"], "default")
        self.assertEqual(res_json["content"], "Hello, world!")
        self.assertIsNone(res_json["referenced_message_id"])
        self.assertIsNotNone(res_json["id"])
        self.assertIsNotNone(res_json["created_at"])
        self.assertIsNotNone(res_json["updated_at"])

    async def test_post_message_to_channel_failure_nonexistent_channel(self):
        """
        Given: 存在しないチャネルIDと有効なメッセージデータ
        When: POST /api/channels/{channel_id}/messages にリクエスト
        Then: 500でサーバーエラーレスポンスが返る
        """

        # Given: 存在しないチャネルIDと有効なメッセージデータ
        nonexistent_channel_id = str(uuid.uuid4())
        message_data = {
            "user_id": str(self.test_user_id),
            "type": "default",
            "content": "Hello, world!",
            "referenced_message_id": None,
        }

        # When: POST /api/channels/{channel_id}/messages にリクエスト
        response = await self.client.post(f"/api/channels/{nonexistent_channel_id}/messages", json=message_data)

        # Then: 500でサーバーエラーレスポンスが返る
        self.assertEqual(response.status_code, 500)
        res_json = response.json()
        self.assertEqual(res_json["detail"], "サーバー内部エラーが発生しました")

    async def test_post_message_to_channel_failure_invalid_user_id(self):
        """
        Given: 有効なチャネルIDと存在しないユーザーIDを含むメッセージデータ
        When: POST /api/channels/{channel_id}/messages にリクエスト
        Then: 500でサーバーエラーレスポンスが返る
        """

        # Given: 有効なチャネルIDと存在しないユーザーIDを含むメッセージデータ
        channel_id = str(self.test_channel_id)
        message_data = {
            "user_id": str(uuid.uuid4()),  # 存在しないユーザーID
            "type": "default",
            "content": "Hello, world!",
            "referenced_message_id": None,
        }

        # When: POST /api/channels/{channel_id}/messages にリクエスト
        response = await self.client.post(f"/api/channels/{channel_id}/messages", json=message_data)

        # Then: 500でサーバーエラーレスポンスが返る
        self.assertEqual(response.status_code, 500)
        res_json = response.json()
        self.assertEqual(res_json["detail"], "サーバー内部エラーが発生しました")

    async def test_post_message_to_channel_failure_missing_required_field(self):
        """
        Given: 有効なチャネルIDと必須フィールドが欠けているメッセージデータ
        When: POST /api/channels/{channel_id}/messages にリクエスト
        Then: 422でバリデーションエラーレスポンスが返る
        """

        # Given: 有効なチャネルIDと必須フィールドが欠けているメッセージデータ
        channel_id = str(self.test_channel_id)
        message_data = {
            "user_id": str(self.test_user_id),
            "type": "default",
            # content フィールドが欠けている
            "referenced_message_id": None,
        }

        # When: POST /api/channels/{channel_id}/messages にリクエスト
        response = await self.client.post(f"/api/channels/{channel_id}/messages", json=message_data)

        # Then: 422でバリデーションエラーレスポンスが返る
        self.assertEqual(response.status_code, 422)
        res_json = response.json()
        self.assertIn("detail", res_json)

    async def test_post_message_to_channel_failure_invalid_uuid_format(self):
        """
        Given: 有効なチャネルIDと不正なUUID形式のuser_idを含むメッセージデータ
        When: POST /api/channels/{channel_id}/messages にリクエスト
        Then: 422でバリデーションエラーレスポンスが返る
        """

        # Given: 有効なチャネルIDと不正なUUID形式のuser_idを含むメッセージデータ
        channel_id = str(self.test_channel_id)
        message_data = {
            "user_id": "invalid-uuid",  # 不正なUUID形式
            "type": "default",
            "content": "Hello, world!",
            "referenced_message_id": None,
        }

        # When: POST /api/channels/{channel_id}/messages にリクエスト
        response = await self.client.post(f"/api/channels/{channel_id}/messages", json=message_data)

        # Then: 422でバリデーションエラーレスポンスが返る
        self.assertEqual(response.status_code, 422)
        res_json = response.json()
        self.assertIn("detail", res_json)


if __name__ == "__main__":
    unittest.main()
