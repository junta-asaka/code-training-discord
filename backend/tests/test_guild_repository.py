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
from domains import Base, Guild, User
from repository.guild_repository import GuildRepositoryIf


class TestGuildRepository(unittest.IsolatedAsyncioTestCase):
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
        self.repository = injector.get(GuildRepositoryIf)

    async def asyncTearDown(self):
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

    async def test_create_guild_success(self):
        """
        Given: 有効なギルド情報
        When: create_guildメソッドを呼び出す
        Then: ギルドが正常に作成されること
        """

        # Given: テスト用ユーザーを作成
        user = await self.create_test_user()

        guild = Guild(
            name="Test Guild",
            owner_user_id=user.id,
        )

        # When: ギルドを作成
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.create_guild(session, guild)

        # Then: ギルドが正常に作成される
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.id)
        self.assertEqual(result.name, "Test Guild")
        self.assertEqual(result.owner_user_id, user.id)
        self.assertIsNotNone(result.created_at)
        self.assertIsNotNone(result.updated_at)

    async def test_create_guild_with_invalid_owner_user_id(self):
        """
        Given: 存在しないオーナーユーザーIDを持つギルド情報
        When: create_guildメソッドを呼び出す
        Then: 外部キー制約エラーが発生すること
        """

        # Given: 存在しないユーザーID
        nonexistent_user_id = uuid.uuid4()

        guild = Guild(
            name="Test Guild",
            owner_user_id=nonexistent_user_id,  # 存在しないユーザーID
        )

        # When/Then: 外部キー制約エラーが発生する
        with self.assertRaises(Exception):  # SQLAlchemy IntegrityError等
            async with self.AsyncSessionLocal() as session:
                await self.repository.create_guild(session, guild)

    async def test_get_guild_by_user_id_name_success(self):
        """
        Given: ユーザーIDとギルド名
        When: get_guild_by_user_id_nameメソッドを呼び出す
        Then: 対応するギルドが取得されること
        """

        # Given: テスト用ユーザーとギルドを作成
        user = await self.create_test_user()
        guild = Guild(name="Test Guild", owner_user_id=user.id)

        async with self.AsyncSessionLocal() as session:
            session.add(guild)
            await session.commit()
            await session.refresh(guild)

        # When: ユーザーIDとギルド名でギルドを検索
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_guild_by_user_id_name(session, str(user.id), "Test Guild")

        # Then: 対応するギルドが取得される
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Test Guild")
        self.assertEqual(result.owner_user_id, user.id)

    async def test_get_guild_by_user_id_name_not_found(self):
        """
        Given: 存在しないユーザーIDまたはギルド名
        When: get_guild_by_user_id_nameメソッドを呼び出す
        Then: Noneが返されること
        """

        # Given: 存在しないユーザーIDとギルド名
        non_existent_user_id = str(uuid.uuid4())
        non_existent_guild_name = "Non Existent Guild"

        # When: 存在しないユーザーIDとギルド名でギルドを検索
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.get_guild_by_user_id_name(
                session, non_existent_user_id, non_existent_guild_name
            )

        # Then: Noneが返される
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
