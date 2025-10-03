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
from domains import Base, Guild, GuildMember, User
from repository.guild_member_repository import GuildMemberRepositoryIf


class TestGuildMemberRepository(unittest.IsolatedAsyncioTestCase):
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
        self.repository = injector.get(GuildMemberRepositoryIf)

    async def asyncTearDown(self):
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

    async def test_create_guild_member_success(self):
        """
        Given: 有効なギルドメンバー情報
        When: create_guild_memberメソッドを呼び出す
        Then: ギルドメンバーが正常に作成されること
        """

        # Given: テスト用ユーザーとギルドを作成
        owner = await self.create_test_user("Owner", "owner")
        user = await self.create_test_user("Member", "member")
        guild = await self.create_test_guild(uuid.UUID(str(owner.id)), "Test Guild")

        guild_member = GuildMember(
            guild_id=uuid.UUID(str(guild.id)),
            user_id=uuid.UUID(str(user.id)),
        )

        # When: ギルドメンバーを作成
        async with self.AsyncSessionLocal() as session:
            result = await self.repository.create_guild_member(session, guild_member)

        # Then: ギルドメンバーが正常に作成される
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.id)
        self.assertEqual(result.guild_id, uuid.UUID(str(guild.id)))
        self.assertEqual(result.user_id, uuid.UUID(str(user.id)))
        self.assertEqual(result.role, "member")  # デフォルト値の確認

    async def test_create_guild_member_duplicate(self):
        """
        Given: 既に存在するギルドメンバーと同じ組み合わせ
        When: create_guild_memberメソッドを再度呼び出す
        Then: 重複制約エラーが発生すること
        """

        # Given: テスト用ユーザー、ギルド、ギルドメンバーを作成
        owner = await self.create_test_user("Owner", "owner")
        user = await self.create_test_user("Member", "member")
        guild = await self.create_test_guild(uuid.UUID(str(owner.id)), "Test Guild")

        guild_member = GuildMember(
            guild_id=uuid.UUID(str(guild.id)),
            user_id=uuid.UUID(str(user.id)),
        )

        # 最初のギルドメンバーを作成
        async with self.AsyncSessionLocal() as session:
            await self.repository.create_guild_member(session, guild_member)
            await session.commit()  # テスト用に明示的にcommit

        # When: 同じ組み合わせでギルドメンバーを再作成
        duplicate_guild_member = GuildMember(
            guild_id=uuid.UUID(str(guild.id)),
            user_id=uuid.UUID(str(user.id)),
        )

        # Then: 重複制約エラーが発生する
        with self.assertRaises(Exception):  # SQLAlchemy IntegrityError等
            async with self.AsyncSessionLocal() as session:
                await self.repository.create_guild_member(session, duplicate_guild_member)


if __name__ == "__main__":
    unittest.main()
