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


class TestChannelAPI(unittest.IsolatedAsyncioTestCase):
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

        # テスト用データを事前に作成
        await self._create_test_data()

    async def _create_test_data(self):
        """テスト用のユーザー、ギルド、チャネル、メッセージデータを作成"""
        async with self.AsyncSessionLocal() as session:
            # テスト用ユーザー作成
            self.test_user_id = uuid.uuid4()
            test_user = User(
                id=self.test_user_id,
                name="Test User",
                username="testuser",
                email="test@example.com",
                password_hash="hashed_password",
                description="Test description",
            )
            session.add(test_user)
            await session.commit()

            # テスト用ギルド作成
            self.test_guild_id = uuid.uuid4()
            test_guild = Guild(
                id=self.test_guild_id,
                name="Test Guild",
                owner_user_id=self.test_user_id,
            )
            session.add(test_guild)
            await session.commit()

            # メッセージありのチャネル作成
            self.test_channel_with_messages_id = uuid.uuid4()
            test_channel_with_messages = Channel(
                id=self.test_channel_with_messages_id,
                guild_id=self.test_guild_id,
                type="text",
                name="general",
                owner_user_id=self.test_user_id,
            )
            session.add(test_channel_with_messages)

            # メッセージなしのチャネル作成
            self.test_channel_empty_id = uuid.uuid4()
            test_channel_empty = Channel(
                id=self.test_channel_empty_id,
                guild_id=self.test_guild_id,
                type="text",
                name="empty-channel",
                owner_user_id=self.test_user_id,
            )
            session.add(test_channel_empty)
            await session.commit()

            # テスト用メッセージ作成（メッセージありチャネル用）
            self.test_message1_id = uuid.uuid4()
            test_message1 = Message(
                id=self.test_message1_id,
                channel_id=self.test_channel_with_messages_id,
                user_id=self.test_user_id,
                type="default",
                content="Hello, world!",
            )
            session.add(test_message1)

            test_message2 = Message(
                id=uuid.uuid4(),
                channel_id=self.test_channel_with_messages_id,
                user_id=self.test_user_id,
                type="default",
                content="How are you?",
            )
            session.add(test_message2)

            # 返信メッセージ
            test_message3 = Message(
                id=uuid.uuid4(),
                channel_id=self.test_channel_with_messages_id,
                user_id=self.test_user_id,
                type="default",
                content="I'm fine, thank you!",
                referenced_message_id=self.test_message1_id,
            )
            session.add(test_message3)

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

    async def test_get_channel_success_with_messages(self):
        """
        Given: メッセージが存在するチャネルID
        When: GET /api/channel にリクエスト
        Then: 201でチャネル情報とメッセージ一覧が返る
        """

        # Given: メッセージが存在するチャネルID
        channel_id = str(self.test_channel_with_messages_id)

        # When: GET /api/channel にリクエスト
        response = await self.client.get(f"/api/channel?channel_id={channel_id}")

        # Then: 201でチャネル情報とメッセージ一覧が返る
        self.assertEqual(response.status_code, 201)
        res_json = response.json()

        self.assertEqual(res_json["id"], channel_id)
        self.assertEqual(res_json["guild_id"], str(self.test_guild_id))
        self.assertEqual(res_json["name"], "general")
        self.assertEqual(len(res_json["messages"]), 3)

        # メッセージの内容確認
        messages = res_json["messages"]
        self.assertEqual(messages[0]["content"], "Hello, world!")
        self.assertEqual(messages[1]["content"], "How are you?")
        self.assertEqual(messages[2]["content"], "I'm fine, thank you!")

        # 返信メッセージの参照確認
        self.assertIsNotNone(messages[2]["referenced_message_id"])
        self.assertEqual(messages[0]["referenced_message_id"], None)
        self.assertEqual(messages[1]["referenced_message_id"], None)

    async def test_get_channel_success_empty_messages(self):
        """
        Given: メッセージが存在しないチャネルID
        When: GET /api/channel にリクエスト
        Then: 201でチャネル情報と空のメッセージ一覧が返る
        """

        # Given: メッセージが存在しないチャネルID
        channel_id = str(self.test_channel_empty_id)

        # When: GET /api/channel にリクエスト
        response = await self.client.get(f"/api/channel?channel_id={channel_id}")

        # Then: 201でチャネル情報と空のメッセージ一覧が返る
        self.assertEqual(response.status_code, 201)
        res_json = response.json()

        self.assertEqual(res_json["id"], channel_id)
        self.assertEqual(res_json["guild_id"], str(self.test_guild_id))
        self.assertEqual(res_json["name"], "empty-channel")
        self.assertEqual(len(res_json["messages"]), 0)

    async def test_get_channel_not_found(self):
        """
        Given: 存在しないチャネルID
        When: GET /api/channel にリクエスト
        Then: 500エラーが返る
        """

        # Given: 存在しないチャネルID
        non_existent_channel_id = str(uuid.uuid4())

        # When: GET /api/channel にリクエスト
        response = await self.client.get(f"/api/channel?channel_id={non_existent_channel_id}")

        # Then: 500エラーが返る
        self.assertEqual(response.status_code, 500)
        res_json = response.json()
        self.assertEqual(res_json["detail"], "サーバー内部エラーが発生しました")


if __name__ == "__main__":
    unittest.main()
