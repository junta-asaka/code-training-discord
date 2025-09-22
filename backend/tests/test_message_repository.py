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
from domains import Base, Channel, Message, User
from repository.message_repository import MessageRepositoryIf


class TestMessageRepository(unittest.IsolatedAsyncioTestCase):
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

        # テスト用DIコンテナからリポジトリを取得
        injector = Injector([configure])
        self.repository = injector.get(MessageRepositoryIf)

    async def asyncTearDown(self):
        # エンジンを非同期に破棄
        await self.engine.dispose()

    async def create_test_user(self) -> User:
        """テスト用ユーザーを作成"""
        user = User(
            name="Test User",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            description="Test description",
        )
        async with self.AsyncSessionLocal() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def create_test_channel(self, owner_user_id: uuid.UUID) -> Channel:
        """テスト用チャネルを作成"""
        channel = Channel(
            type="text",
            name="test-channel",
            owner_user_id=owner_user_id,
        )
        async with self.AsyncSessionLocal() as session:
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            return channel

    async def test_create_message_success(self):
        """
        Given: 有効なメッセージ情報
        When: create_messageメソッドを呼び出す
        Then: メッセージが正常に作成されること
        """

        # Given: テスト用ユーザーとチャネルを作成
        user = await self.create_test_user()
        channel = await self.create_test_channel(uuid.UUID(str(user.id)))

        message = Message(
            channel_id=channel.id,
            author_user_id=user.id,
            type="default",
            content="Hello, World!",
        )

        # When: メッセージを作成
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.create_message(session, message)

        # Then: メッセージが正常に作成される
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.id)
        self.assertEqual(result.channel_id, channel.id)
        self.assertEqual(result.author_user_id, user.id)
        self.assertEqual(result.type, "default")
        self.assertEqual(result.content, "Hello, World!")
        self.assertIsNotNone(result.created_at)
        self.assertIsNotNone(result.updated_at)

    async def test_create_message_empty_content(self):
        """
        Given: 内容が空のメッセージ情報
        When: create_messageメソッドを呼び出す
        Then: メッセージが正常に作成されること（内容が空でも可）
        """

        # Given: テスト用ユーザーとチャネルを作成
        user = await self.create_test_user()
        channel = await self.create_test_channel(uuid.UUID(str(user.id)))

        message = Message(
            channel_id=channel.id,
            author_user_id=user.id,
            type="default",
            content="",  # 空の内容
        )

        # When: メッセージを作成
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.create_message(session, message)

        # Then: メッセージが正常に作成される
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.id)
        self.assertEqual(result.channel_id, channel.id)
        self.assertEqual(result.author_user_id, user.id)
        self.assertEqual(result.type, "default")
        self.assertEqual(result.content, "")
        self.assertIsNotNone(result.created_at)
        self.assertIsNotNone(result.updated_at)

    async def test_create_message_with_invalid_channel_id(self):
        """
        Given: 存在しないチャネルIDを持つメッセージ情報
        When: create_messageメソッドを呼び出す
        Then: 外部キー制約エラーが発生すること
        """

        # Given: テスト用ユーザーを作成（チャネルは作成しない）
        user = await self.create_test_user()
        nonexistent_channel_id = uuid.uuid4()

        message = Message(
            channel_id=nonexistent_channel_id,  # 存在しないチャネルID
            author_user_id=user.id,
            type="default",
            content="Test message",
        )

        # When/Then: 外部キー制約エラーが発生する
        with self.assertRaises(Exception):  # SQLAlchemy IntegrityError等
            async with self.AsyncSessionLocal() as session:
                await self.repository.create_message(session, message)


if __name__ == "__main__":
    unittest.main()
