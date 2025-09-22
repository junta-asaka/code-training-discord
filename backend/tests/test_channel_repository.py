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
from domains import Base, Channel, Guild, GuildMember, User
from repository.channel_repository import ChannelRepositoryIf


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
            await conn.execute(text("DELETE FROM messages"))
            await conn.execute(text("DELETE FROM channels"))
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

        # When/Then: 外部キー制約エラーが発生する
        with self.assertRaises(Exception):  # SQLAlchemy IntegrityError等
            async with self.AsyncSessionLocal() as session:
                await self.repository.create_channel(session, channel)

    async def test_get_channels_by_user_ids_type_name_success_with_guild(self):
        """
        Given: ギルドメンバーとして登録されたユーザーが所属するギルドのチャネル
        When: get_channels_by_user_ids_type_nameメソッドを呼び出す
        Then: 条件に一致するチャネルが取得されること
        """

        # Given: テスト環境をセットアップ
        owner = await self.create_test_user("Owner", "owner")
        member = await self.create_test_user("Member", "member")
        guild = await self.create_test_guild(uuid.UUID(str(owner.id)), "Test Guild")
        await self.create_test_guild_member(uuid.UUID(str(guild.id)), uuid.UUID(str(member.id)))

        # ギルドに関連付けられたチャネルを作成
        channel = Channel(
            type="text",
            name="general",
            owner_user_id=uuid.UUID(str(owner.id)),
            guild_id=uuid.UUID(str(guild.id)),
        )
        async with self.AsyncSessionLocal() as session:
            await self.repository.create_channel(session, channel)

        # When: メンバーのユーザーIDで検索
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_channels_by_user_ids_type_name(
                session, user_ids=[str(member.id)], type="text", name="general"
            )

        # Then: チャネルが取得される
        self.assertIsNotNone(result)
        self.assertEqual(result.type, "text")
        self.assertEqual(result.name, "general")
        self.assertEqual(result.guild_id, uuid.UUID(str(guild.id)))

    async def test_get_channels_by_user_ids_type_name_no_match_conditions(self):
        """
        Given: ユーザーは所属しているが、条件（タイプや名前）に一致しないチャネル
        When: get_channels_by_user_ids_type_nameメソッドを呼び出す
        Then: Noneが返されること
        """

        # Given: テスト環境をセットアップ
        owner = await self.create_test_user("Owner", "owner")
        member = await self.create_test_user("Member", "member")
        guild = await self.create_test_guild(uuid.UUID(str(owner.id)), "Test Guild")
        await self.create_test_guild_member(uuid.UUID(str(guild.id)), uuid.UUID(str(member.id)))

        # ギルドに関連付けられたチャネルを作成
        channel = Channel(
            type="text",
            name="general",
            owner_user_id=uuid.UUID(str(owner.id)),
            guild_id=uuid.UUID(str(guild.id)),
        )
        async with self.AsyncSessionLocal() as session:
            await self.repository.create_channel(session, channel)

        # When: 存在しないタイプで検索
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_channels_by_user_ids_type_name(
                session,
                user_ids=[str(member.id)],
                type="voice",  # 実際は text タイプのチャネルのみ存在
                name="general",
            )

        # Then: 条件に一致しないためNoneが返される
        self.assertIsNone(result)

    async def test_get_channels_by_user_ids_type_name_nonexistent_user(self):
        """
        Given: 存在しないユーザーID
        When: get_channels_by_user_ids_type_nameメソッドを呼び出す
        Then: Noneが返されること
        """

        # Given: 存在しないユーザーID
        nonexistent_user_id = str(uuid.uuid4())

        # When: 存在しないユーザーIDで検索
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_channels_by_user_ids_type_name(
                session, user_ids=[nonexistent_user_id], type="text", name="general"
            )

        # Then: Noneが返される
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
