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
from domains import Base, Channel, Guild, GuildMember, Message, User
from repository.channel_repository import (
    ChannelCreateError,
    ChannelNotFoundError,
    ChannelRepositoryIf,
)


class TestChannelRepository(unittest.IsolatedAsyncioTestCase):
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
        self.repository = injector.get(ChannelRepositoryIf)

    async def asyncTearDown(self):
        # エンジンを非同期に破棄
        await self.engine.dispose()

    async def create_test_user(self, name: str = "Test User", username: str = "testuser") -> User:
        """テスト用ユーザーを作成"""
        user = User(
            name=name,
            username=username,
            email=f"{username}@example.com",
            password_hash="hashed_password",
            description="Test description",
        )
        async with self.AsyncSessionLocal() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def create_test_guild(self, owner_user_id: uuid.UUID, name: str = "Test Guild") -> Guild:
        """テスト用ギルドを作成"""
        guild = Guild(
            name=name,
            owner_user_id=owner_user_id,
        )
        async with self.AsyncSessionLocal() as session:
            session.add(guild)
            await session.commit()
            await session.refresh(guild)
            return guild

    async def create_test_guild_member(self, guild_id: uuid.UUID, user_id: uuid.UUID) -> GuildMember:
        """テスト用ギルドメンバーを作成"""
        guild_member = GuildMember(
            guild_id=guild_id,
            user_id=user_id,
        )
        async with self.AsyncSessionLocal() as session:
            session.add(guild_member)
            await session.commit()
            await session.refresh(guild_member)
            return guild_member

    async def test_create_channel_success(self):
        """
        Given: 有効なチャネル情報
        When: create_channelメソッドを呼び出す
        Then: チャネルが正常に作成されること
        """

        # Given: テスト用ユーザーを作成
        owner = await self.create_test_user("Owner", "owner")

        channel = Channel(
            type="text",
            name="general",
            owner_user_id=uuid.UUID(str(owner.id)),
        )

        # When: チャネルを作成
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.create_channel(session, channel)

        # Then: チャネルが正常に作成される
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.id)
        self.assertEqual(result.type, "text")
        self.assertEqual(result.name, "general")
        self.assertEqual(result.owner_user_id, uuid.UUID(str(owner.id)))
        self.assertIsNotNone(result.created_at)
        self.assertIsNotNone(result.updated_at)

    async def test_create_channel_duplicate_name_same_owner(self):
        """
        Given: 同じオーナーが同じ名前のチャネルを作成しようとする
        When: create_channelメソッドを呼び出す
        Then: 2つ目のチャネルも正常に作成されること（同じ名前でも異なるIDで作成可能）
        """

        # Given: テスト用ユーザーを作成
        owner = await self.create_test_user("Owner", "owner")

        # 最初のチャネルを作成
        first_channel = Channel(
            type="text",
            name="general",
            owner_user_id=uuid.UUID(str(owner.id)),
        )
        async with self.AsyncSessionLocal() as session:
            first_result = await self.repository.create_channel(session, first_channel)

        # When: 同じ名前の2つ目のチャネルを作成
        second_channel = Channel(
            type="text",
            name="general",  # 同じ名前
            owner_user_id=uuid.UUID(str(owner.id)),
        )
        async with self.AsyncSessionLocal() as session:
            second_result = await self.repository.create_channel(session, second_channel)

        # Then: 両方のチャネルが正常に作成される（異なるID）
        self.assertIsNotNone(first_result)
        self.assertIsNotNone(second_result)
        self.assertNotEqual(first_result.id, second_result.id)
        self.assertEqual(first_result.name, second_result.name)
        self.assertEqual(first_result.owner_user_id, second_result.owner_user_id)

    async def test_create_channel_with_invalid_owner(self):
        """
        Given: 存在しないオーナーユーザーIDを持つチャネル情報
        When: create_channelメソッドを呼び出す
        Then: 外部キー制約エラーが発生すること
        """

        # Given: 存在しないユーザーID
        nonexistent_user_id = uuid.uuid4()

        channel = Channel(
            type="text",
            name="test-channel",
            owner_user_id=nonexistent_user_id,
        )

        # When/Then: ChannelCreateErrorが発生する
        with self.assertRaises(ChannelCreateError) as context:
            async with self.AsyncSessionLocal() as session:
                await self.repository.create_channel(session, channel)

        # エラーメッセージに適切な情報が含まれていることを確認
        error_message = str(context.exception)
        self.assertIn("データベース制約違反", error_message)

        # 元の例外が保持されていることを確認
        self.assertIsNotNone(context.exception.original_error)

    async def test_get_channel_by_id_success(self):
        """
        Given: 存在するチャネルID
        When: get_channel_by_idメソッドを呼び出す
        Then: 対応するチャネルが取得されること
        """

        # Given: テスト用ユーザーとチャネルを作成
        owner = await self.create_test_user("Owner", "owner")
        channel = Channel(
            type="text",
            name="test-channel",
            owner_user_id=uuid.UUID(str(owner.id)),
        )

        async with self.AsyncSessionLocal() as session:
            created_channel = await self.repository.create_channel(session, channel)

        # When: チャネルIDでチャネルを取得
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_channel_by_id(session, str(created_channel.id))

        # Then: 正しいチャネルが取得される
        self.assertIsNotNone(result)
        if result is not None:
            self.assertEqual(result.id, created_channel.id)
            self.assertEqual(result.type, "text")
            self.assertEqual(result.name, "test-channel")
            self.assertEqual(result.owner_user_id, uuid.UUID(str(owner.id)))

    async def test_get_channel_by_id_nonexistent_channel(self):
        """
        Given: 存在しないチャネルID
        When: get_channel_by_idメソッドを呼び出す
        Then: Noneが返されること
        """

        # Given: 存在しないチャネルID
        nonexistent_channel_id = str(uuid.uuid4())

        # When: 存在しないチャネルIDでチャネルを取得
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_channel_by_id(session, nonexistent_channel_id)

        # Then: Noneが返される
        self.assertIsNone(result)

    async def test_update_last_message_id_success(self):
        """
        Given: 存在するチャネルIDと有効なメッセージID
        When: update_last_message_idメソッドを呼び出す
        Then: チャネルのlast_message_idが正常に更新されること
        """

        # Given: テスト用ユーザーとチャネルを作成
        owner = await self.create_test_user("Owner", "owner")
        channel = Channel(
            type="text",
            name="test-channel",
            owner_user_id=uuid.UUID(str(owner.id)),
        )

        async with self.AsyncSessionLocal() as session:
            created_channel = await self.repository.create_channel(session, channel)

        message = Message(
            channel_id=created_channel.id,
            user_id=owner.id,
            type="default",
            content="Test message",
        )

        async with self.AsyncSessionLocal() as session:
            session.add(message)
            await session.commit()
            await session.refresh(message)
            test_message_id = str(message.id)

        # When: last_message_idを更新
        async with self.AsyncSessionLocal() as session:
            await self.repository.update_last_message_id(session, str(created_channel.id), test_message_id)
            await session.commit()

        # Then: チャネルのlast_message_idが更新されていることを確認
        async with self.AsyncSessionLocal() as session:
            updated_channel = await self.repository.get_channel_by_id(session, str(created_channel.id))

        self.assertIsNotNone(updated_channel)
        if updated_channel is not None:
            self.assertEqual(str(updated_channel.last_message_id), test_message_id)

    async def test_update_last_message_id_nonexistent_channel(self):
        """
        Given: 存在しないチャネルIDと有効なメッセージID
        When: update_last_message_idメソッドを呼び出す
        Then: ChannelNotFoundErrorが発生すること
        """

        # Given: 存在しないチャネルIDとメッセージID
        nonexistent_channel_id = str(uuid.uuid4())
        test_message_id = str(uuid.uuid4())

        # When/Then: ChannelNotFoundErrorが発生する
        with self.assertRaises(ChannelNotFoundError) as context:
            async with self.AsyncSessionLocal() as session:
                await self.repository.update_last_message_id(session, nonexistent_channel_id, test_message_id)

        # エラーメッセージに適切な情報が含まれていることを確認
        error_message = str(context.exception)
        self.assertIn("指定されたチャンネルが存在しません", error_message)
        self.assertIn(nonexistent_channel_id, error_message)

    async def test_update_last_message_id_multiple_updates(self):
        """
        Given: 存在するチャネルIDと複数のメッセージID
        When: update_last_message_idメソッドを複数回呼び出す
        Then: 最後に更新されたメッセージIDが設定されていること
        """

        # Given: テスト用ユーザーとチャネルを作成
        owner = await self.create_test_user("Owner", "owner")
        channel = Channel(
            type="text",
            name="test-channel",
            owner_user_id=uuid.UUID(str(owner.id)),
        )

        async with self.AsyncSessionLocal() as session:
            created_channel = await self.repository.create_channel(session, channel)

        first_message = Message(
            channel_id=created_channel.id,
            user_id=owner.id,
            type="default",
            content="First message",
        )

        second_message = Message(
            channel_id=created_channel.id,
            user_id=owner.id,
            type="default",
            content="Second message",
        )

        final_message = Message(
            channel_id=created_channel.id,
            user_id=owner.id,
            type="default",
            content="Final message",
        )

        async with self.AsyncSessionLocal() as session:
            session.add(first_message)
            session.add(second_message)
            session.add(final_message)
            await session.commit()
            await session.refresh(first_message)
            await session.refresh(second_message)
            await session.refresh(final_message)

        first_message_id = str(first_message.id)
        second_message_id = str(second_message.id)
        final_message_id = str(final_message.id)

        # When: 複数回更新
        async with self.AsyncSessionLocal() as session:
            await self.repository.update_last_message_id(session, str(created_channel.id), first_message_id)
            await session.commit()

        async with self.AsyncSessionLocal() as session:
            await self.repository.update_last_message_id(session, str(created_channel.id), second_message_id)
            await session.commit()

        async with self.AsyncSessionLocal() as session:
            await self.repository.update_last_message_id(session, str(created_channel.id), final_message_id)
            await session.commit()

        # Then: 最後に設定されたメッセージIDが保存されていることを確認
        async with self.AsyncSessionLocal() as session:
            updated_channel = await self.repository.get_channel_by_id(session, str(created_channel.id))

        self.assertIsNotNone(updated_channel)
        if updated_channel is not None:
            self.assertEqual(str(updated_channel.last_message_id), final_message_id)


if __name__ == "__main__":
    unittest.main()
