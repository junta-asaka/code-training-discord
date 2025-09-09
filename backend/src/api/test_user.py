import os
import unittest
from typing import AsyncGenerator
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from main import app
from database import get_session
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker


class TestUserAPI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        load_dotenv()
        DATABASE_URL = os.environ["DATABASE_URL"]
        self.engine = create_async_engine(DATABASE_URL, echo=True, future=True)
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
        )
        # テーブル作成
        from domains import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # テーブルクリーンアップ処理を実行
        async with self.engine.begin() as conn:
            # 外部キー制約のため、子テーブルから削除
            await conn.execute(text("DELETE FROM messages"))
            await conn.execute(text("DELETE FROM channels"))
            await conn.execute(text("DELETE FROM friends"))
            await conn.execute(text("DELETE FROM sessions"))
            await conn.execute(text("DELETE FROM users"))

        # テスト用のデータベースセッション依存関数をオーバーライド
        async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
            async with self.AsyncSessionLocal() as session:
                yield session
        
        app.dependency_overrides[get_session] = override_get_session
        
        # 非同期でAsyncClientを初期化
        self.client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        )

    async def asyncTearDown(self):
        # 依存関数のオーバーライドを削除
        app.dependency_overrides.clear()
        # クライアントを非同期に破棄
        await self.client.aclose()
        # エンジンを非同期に破棄
        await self.engine.dispose()

    async def test_create_user_success(self):
        """
        Given: 新規ユーザー情報
        When: POST /user にリクエスト
        Then: 201でユーザー情報が返る
        """

        # Given: 新規ユーザー情報
        data = {
            "name": "Test User",
            "username": "testuser",
            "email": "test@example.com",
            "password": "hashed_password",
            "description": "Test description",
        }

        # When: POST /user にリクエスト
        response = await self.client.post("/user", json=data)

        # Then: 201でユーザー情報が返る
        self.assertEqual(response.status_code, 201)
        res_json = response.json()
        self.assertEqual(res_json["name"], data["name"])
        self.assertEqual(res_json["username"], data["username"])
        self.assertEqual(res_json["email"], data["email"])
        self.assertEqual(res_json["description"], data["description"])
        self.assertIn("id", res_json)
        self.assertIn("created_at", res_json)
        self.assertIn("updated_at", res_json)

    async def test_create_user_duplicate_username(self):
        """
        Given: 重複ユーザー情報
        When: POST /user に2回リクエスト
        Then: 2回目のリクエストで400エラーが返る
        """

        # Given: 重複ユーザー情報
        data = {
            "name": "Test User",
            "username": "testuser",
            "email": "test@example.com",
            "password": "hashed_password",
            "description": "Test description",
        }

        # Given: POST /user に2回リクエスト
        # 1回目
        response1 = await self.client.post("/user", json=data)
        self.assertEqual(response1.status_code, 201)
        # 2回目
        response2 = await self.client.post("/user", json=data)

        # Then: 400エラー
        self.assertEqual(response2.status_code, 400)
        self.assertIn("detail", response2.json())


if __name__ == "__main__":
    unittest.main()
