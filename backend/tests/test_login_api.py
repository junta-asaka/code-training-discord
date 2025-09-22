import os
import sys
import unittest
from typing import AsyncGenerator

from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# テストファイルのルートディレクトリからの相対パスでsrcフォルダを指定
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from database import get_session
from domains import Base
from main import app


class TestLoginAPI(unittest.IsolatedAsyncioTestCase):
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

        # テスト用ユーザーを事前に作成
        await self._create_test_user()

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

    async def _create_test_user(self):
        """テスト用ユーザーを作成"""
        user_data = {
            "name": "Test User",
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
            "description": "",
        }
        await self.client.post("/user", json=user_data)

    async def test_post_login_success(self):
        """
        Given: 正しいユーザー情報
        When: POST /login にフォームデータでリクエスト
        Then: 200でログイン成功レスポンスが返る
        """

        # Given: 正しいユーザー情報
        login_data = {"username": "testuser", "password": "testpassword"}

        # When: POST /login にフォームデータでリクエスト
        response = await self.client.post("/login", data=login_data)

        # Then: 200でログイン成功レスポンスが返る
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertEqual(res_json["name"], "Test User")
        self.assertEqual(res_json["username"], "testuser")
        self.assertIn("access_token", res_json)
        self.assertEqual(res_json["token_type"], "bearer")
        self.assertIsNone(res_json["next"])

    async def test_post_login_success_with_next_param(self):
        """
        Given: 正しいユーザー情報とnextパラメータ
        When: POST /login?next=/dashboard にフォームデータでリクエスト
        Then: 200でログイン成功レスポンス（nextパラメータ含む）が返る
        """

        # Given: 正しいユーザー情報とnextパラメータ
        login_data = {"username": "testuser", "password": "testpassword"}

        # When: POST /login?next=/dashboard にフォームデータでリクエスト
        response = await self.client.post("/login?next=/dashboard", data=login_data)

        # Then: 200でログイン成功レスポンス（nextパラメータ含む）が返る
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertEqual(res_json["name"], "Test User")
        self.assertEqual(res_json["username"], "testuser")
        self.assertIn("access_token", res_json)
        self.assertEqual(res_json["token_type"], "bearer")
        self.assertEqual(res_json["next"], "/dashboard")

    async def test_post_login_invalid_username(self):
        """
        Given: 存在しないユーザー名
        When: POST /login にフォームデータでリクエスト
        Then: 401で認証失敗エラーが返る
        """

        # Given: 存在しないユーザー名
        login_data = {"username": "nonexistentuser", "password": "testpassword"}

        # When: POST /login にフォームデータでリクエスト
        response = await self.client.post("/login", data=login_data)

        # Then: 401で認証失敗エラーが返る
        self.assertEqual(response.status_code, 401)
        res_json = response.json()
        self.assertEqual(res_json["detail"]["message"], "Unauthorized")

    async def test_post_login_invalid_password(self):
        """
        Given: 正しいユーザー名と間違ったパスワード
        When: POST /login にフォームデータでリクエスト
        Then: 401で認証失敗エラーが返る
        """

        # Given: 正しいユーザー名と間違ったパスワード
        login_data = {"username": "testuser", "password": "wrongpassword"}

        # When: POST /login にフォームデータでリクエスト
        response = await self.client.post("/login", data=login_data)

        # Then: 401で認証失敗エラーが返る
        self.assertEqual(response.status_code, 401)
        res_json = response.json()
        self.assertEqual(res_json["detail"]["message"], "Unauthorized")

    async def test_post_login_invalid_credentials_with_next_param(self):
        """
        Given: 間違った認証情報とnextパラメータ
        When: POST /login?next=/dashboard にフォームデータでリクエスト
        Then: 401で認証失敗エラー（nextパラメータ含む）が返る
        """

        # Given: 間違った認証情報とnextパラメータ
        login_data = {"username": "testuser", "password": "wrongpassword"}

        # When: POST /login?next=/dashboard にフォームデータでリクエスト
        response = await self.client.post("/login?next=/dashboard", data=login_data)

        # Then: 401で認証失敗エラー（nextパラメータ含む）が返る
        self.assertEqual(response.status_code, 401)
        res_json = response.json()
        self.assertEqual(res_json["detail"]["message"], "Unauthorized")
        self.assertEqual(res_json["detail"]["next"], "/dashboard")

    async def test_post_login_empty_username(self):
        """
        Given: 空のユーザー名
        When: POST /login にフォームデータでリクエスト
        Then: 422でバリデーションエラーが返る
        """

        # Given: 空のユーザー名
        login_data = {"username": "", "password": "testpassword"}

        # When: POST /login にフォームデータでリクエスト
        response = await self.client.post("/login", data=login_data)

        # Then: 401で認証失敗エラーが返る
        self.assertEqual(response.status_code, 401)
        res_json = response.json()
        self.assertEqual(res_json["detail"]["message"], "Unauthorized")

    async def test_post_login_empty_password(self):
        """
        Given: 空のパスワード
        When: POST /login にフォームデータでリクエスト
        Then: 422でバリデーションエラーが返る
        """

        # Given: 空のパスワード
        login_data = {"username": "testuser", "password": ""}

        # When: POST /login にフォームデータでリクエスト
        response = await self.client.post("/login", data=login_data)

        # Then: 401で認証失敗エラーが返る
        self.assertEqual(response.status_code, 401)
        res_json = response.json()
        self.assertEqual(res_json["detail"]["message"], "Unauthorized")

    async def test_post_login_missing_username(self):
        """
        Given: usernameフィールドがない
        When: POST /login にフォームデータでリクエスト
        Then: 422でバリデーションエラーが返る
        """

        # Given: usernameフィールドがない
        login_data = {"password": "testpassword"}

        # When: POST /login にフォームデータでリクエスト
        response = await self.client.post("/login", data=login_data)

        # Then: 422でバリデーションエラーが返る
        self.assertEqual(response.status_code, 422)

    async def test_post_login_missing_password(self):
        """
        Given: passwordフィールドがない
        When: POST /login にフォームデータでリクエスト
        Then: 422でバリデーションエラーが返る
        """

        # Given: passwordフィールドがない
        login_data = {"username": "testuser"}

        # When: POST /login にフォームデータでリクエスト
        response = await self.client.post("/login", data=login_data)

        # Then: 422でバリデーションエラーが返る
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
