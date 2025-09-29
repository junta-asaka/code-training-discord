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


class TestFriendAPI(unittest.IsolatedAsyncioTestCase):
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
            await conn.execute(text("DELETE FROM channels"))
            await conn.execute(text("DELETE FROM messages"))
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

    async def _create_test_user(self, name: str, username: str, email: str) -> dict:
        """テスト用ユーザーを作成し、レスポンスを返す"""
        user_data = {
            "name": name,
            "username": username,
            "email": email,
            "password": "testpassword",
            "description": "Test description",
        }
        response = await self.client.post("/user", json=user_data)
        return response.json()

    async def _create_test_users(self):
        """テスト用ユーザーを複数作成"""
        self.user1 = await self._create_test_user("Test User 1", "testuser1", "test1@example.com")
        self.user2 = await self._create_test_user("Test User 2", "testuser2", "test2@example.com")
        self.user3 = await self._create_test_user("Test User 3", "testuser3", "test3@example.com")

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

    async def test_create_friend_success(self):
        """
        Given: 正常なフレンド作成リクエスト
        When: POST /api/friend にリクエスト
        Then: 201でフレンド作成レスポンスが返る
        """

        # Given: テスト用ユーザーを事前に作成
        await self._create_test_users()

        friend_data = {"username": "testuser1", "related_username": "testuser2", "type": "friend"}

        # When: POST /api/friend にリクエスト
        response = await self.client.post("/api/friend", json=friend_data)

        # Then: 201でフレンド作成レスポンスが返る
        self.assertEqual(response.status_code, 201)
        res_json = response.json()
        self.assertIn("id", res_json)
        self.assertEqual(res_json["user_id"], self.user1["id"])
        self.assertEqual(res_json["related_user_id"], self.user2["id"])
        self.assertEqual(res_json["type"], "friend")
        self.assertIn("created_at", res_json)

    async def test_create_friend_failure(self):
        """
        Given: フレンド作成に失敗するケース（ユーザーが存在しない等）
        When: POST /api/friend にリクエスト
        Then: 400でエラーレスポンスが返る
        """

        # Given: 存在しないユーザーでフレンド作成を試行
        friend_data = {"username": "nonexistentuser", "related_username": "testuser2", "type": "friend"}

        # When: POST /api/friend にリクエスト
        response = await self.client.post("/api/friend", json=friend_data)

        # Then: 400でエラーレスポンスが返る
        self.assertEqual(response.status_code, 400)
        res_json = response.json()
        self.assertEqual(res_json["detail"], "Failed to create friend")

    async def test_create_friend_missing_username(self):
        """
        Given: usernameフィールドがないリクエスト
        When: POST /api/friend にリクエスト
        Then: 422でバリデーションエラーが返る
        """

        # Given: usernameフィールドがないリクエスト
        friend_data = {"related_username": "testuser2", "type": "friend"}

        # When: POST /api/friend にリクエスト
        response = await self.client.post("/api/friend", json=friend_data)

        # Then: 422でバリデーションエラーが返る
        self.assertEqual(response.status_code, 422)

    async def test_create_friend_missing_related_username(self):
        """
        Given: related_usernameフィールドがないリクエスト
        When: POST /api/friend にリクエスト
        Then: 422でバリデーションエラーが返る
        """

        # Given: related_usernameフィールドがないリクエスト
        friend_data = {"username": "testuser1", "type": "friend"}

        # When: POST /api/friend にリクエスト
        response = await self.client.post("/api/friend", json=friend_data)

        # Then: 422でバリデーションエラーが返る
        self.assertEqual(response.status_code, 422)

    async def test_create_friend_empty_username(self):
        """
        Given: 空のusername
        When: POST /api/friend にリクエスト
        Then: 400でエラーが返る
        """

        # Given: 空のusername
        friend_data = {"username": "", "related_username": "testuser2", "type": "friend"}

        # When: POST /api/friend にリクエスト
        response = await self.client.post("/api/friend", json=friend_data)

        # Then: 400でエラーが返る
        self.assertEqual(response.status_code, 400)

    # GET /api/friends のテスト
    async def test_get_friends_success_multiple(self):
        """
        Given: 複数のフレンドが存在するユーザー
        When: GET /api/friends にリクエスト
        Then: 200でフレンド一覧レスポンスが返る
        """

        # Given: テスト用ユーザーを作成し、フレンド関係を設定
        await self._create_test_users()

        # user1とuser2, user3をフレンドにする
        await self.client.post(
            "/api/friend", json={"username": "testuser1", "related_username": "testuser2", "type": "friend"}
        )
        await self.client.post(
            "/api/friend", json={"username": "testuser1", "related_username": "testuser3", "type": "friend"}
        )

        # When: GET /api/friends にリクエスト
        response = await self.client.get(f"/api/friends?user_id={self.user1['id']}")

        # Then: 200でフレンド一覧レスポンスが返る
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertEqual(len(res_json), 2)

        # レスポンスの内容を確認（順序は保証されないため、名前で確認）
        friend_names = [friend["name"] for friend in res_json]
        self.assertIn("Test User 2", friend_names)
        self.assertIn("Test User 3", friend_names)

    async def test_get_friends_empty_list(self):
        """
        Given: フレンドが存在しないユーザー
        When: GET /api/friends にリクエスト
        Then: 200で空のリストが返る
        """

        # Given: フレンドが存在しないユーザー
        await self._create_test_users()

        # When: GET /api/friends にリクエスト
        response = await self.client.get(f"/api/friends?user_id={self.user1['id']}")

        # Then: 200で空のリストが返る
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertEqual(res_json, [])

    async def test_get_friends_empty_user_list(self):
        """
        Given: 存在しないユーザーIDでリクエスト
        When: GET /api/friends にリクエスト
        Then: 200で空のリストが返る
        """

        # Given: 存在しないユーザーIDでリクエスト
        nonexistent_user_id = "00000000-0000-0000-0000-000000000000"

        # When: GET /api/friends にリクエスト
        response = await self.client.get(f"/api/friends?user_id={nonexistent_user_id}")

        # Then: 200で空のリストが返る
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertEqual(res_json, [])

    async def test_get_friends_missing_user_id(self):
        """
        Given: user_idパラメータがないリクエスト
        When: GET /api/friends にリクエスト
        Then: 422でバリデーションエラーが返る
        """

        # Given: user_idパラメータがないリクエスト
        # When: GET /api/friends にリクエスト
        response = await self.client.get("/api/friends")

        # Then: 422でバリデーションエラーが返る
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
