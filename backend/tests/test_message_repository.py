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
from repository.message_repository import MessageCreateError, MessageRepositoryIf


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
            await conn.execute(text("DELETE FROM channels"))
            await conn.execute(text("DELETE FROM messages"))
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
            user_id=user.id,
            type="default",
            content="Hello, World!",
        )

        # When: メッセージを作成
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.create_message(session, message)
            await session.commit()  # データを永続化

        # Then: メッセージが正常に作成される
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.id)
        self.assertEqual(result.channel_id, channel.id)
        self.assertEqual(result.user_id, user.id)
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
            user_id=user.id,
            type="default",
            content="",  # 空の内容
        )

        # When: メッセージを作成
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.create_message(session, message)
            await session.commit()  # データを永続化

        # Then: メッセージが正常に作成される
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.id)
        self.assertEqual(result.channel_id, channel.id)
        self.assertEqual(result.user_id, user.id)
        self.assertEqual(result.type, "default")
        self.assertEqual(result.content, "")
        self.assertIsNotNone(result.created_at)
        self.assertIsNotNone(result.updated_at)

    async def test_create_message_with_invalid_channel_id(self):
        """
        Given: 存在しないチャネルIDを持つメッセージ情報
        When: create_messageメソッドを呼び出す
        Then: MessageDatabaseConstraintErrorが発生すること
        """

        # Given: テスト用ユーザーを作成（チャネルは作成しない）
        user = await self.create_test_user()
        nonexistent_channel_id = uuid.uuid4()

        message = Message(
            channel_id=nonexistent_channel_id,  # 存在しないチャネルID
            user_id=user.id,
            type="default",
            content="Test message",
        )

        # When/Then: MessageCreateErrorが発生する
        with self.assertRaises(MessageCreateError) as context:
            async with self.AsyncSessionLocal() as session:
                await self.repository.create_message(session, message)

        # エラーメッセージに適切な情報が含まれていることを確認
        error_message = str(context.exception)
        self.assertIn("データベース制約違反", error_message)
        print(context.exception.original_error)

        # 元の例外が保持されていることを確認
        self.assertIsNotNone(context.exception.original_error)

    async def test_get_message_by_channel_id_success(self):
        """
        Given: チャネルに複数のメッセージが存在する
        When: get_message_by_channel_idメソッドを呼び出す
        Then: 作成日時順にメッセージリストが取得されること
        """

        # Given: テスト用ユーザーとチャネルを作成
        user = await self.create_test_user()
        channel = await self.create_test_channel(uuid.UUID(str(user.id)))

        # 複数のメッセージを作成
        messages = [
            Message(
                channel_id=channel.id,
                user_id=user.id,
                type="default",
                content="First message",
            ),
            Message(
                channel_id=channel.id,
                user_id=user.id,
                type="default",
                content="Second message",
            ),
            Message(
                channel_id=channel.id,
                user_id=user.id,
                type="default",
                content="Third message",
            ),
        ]

        # メッセージを順番に作成
        async with self.AsyncSessionLocal() as session:
            for message in messages:
                await self.repository.create_message(session, message)
            # 全てのメッセージ作成後にコミット
            await session.commit()

        # When: チャネルIDでメッセージを取得
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_message_by_channel_id(session, str(channel.id))

        # Then: メッセージが作成日時順に取得される
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].content, "First message")
        self.assertEqual(result[1].content, "Second message")
        self.assertEqual(result[2].content, "Third message")

        # 全てのメッセージが同じチャネルIDを持つことを確認
        for message in result:
            self.assertEqual(message.channel_id, channel.id)

    async def test_get_message_by_channel_id_nonexistent_channel(self):
        """
        Given: 存在しないチャネルID
        When: get_message_by_channel_idメソッドを呼び出す
        Then: 空のリストが返されること
        """

        # Given: 存在しないチャネルID
        nonexistent_channel_id = uuid.uuid4()

        # When: 存在しないチャネルIDでメッセージを取得
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_message_by_channel_id(session, str(nonexistent_channel_id))

        # Then: 空のリストが返される
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()
