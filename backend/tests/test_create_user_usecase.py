import base64
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from injector import Injector
from sqlalchemy.ext.asyncio import AsyncSession

# テストファイルのルートディレクトリからの相対パスでsrcフォルダを指定
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from dependencies import configure
from domains import Guild, GuildMember, User
from schema.user_schema import UserCreateRequest, UserResponse
from usecase.create_user import CreateUserUseCaseIf
from utils.utils import hash_password


class TestCreateUserUseCaseImpl(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # テスト用DIコンテナからユースケースを取得
        injector = Injector([configure])
        self.use_case = injector.get(CreateUserUseCaseIf)
        self.mock_session = Mock(spec=AsyncSession)

    # リポジトリのみモックをパッチ
    @patch("usecase.create_user.GuildMemberRepositoryIf")
    @patch("usecase.create_user.GuildRepositoryIf")
    @patch("usecase.create_user.UserRepositoryIf")
    async def test_execute_success(
        self, mock_user_repository_class, mock_guild_repository_class, mock_guild_member_repository_class
    ):
        """
        Given: 有効なユーザー作成リクエスト
        When: executeメソッドを呼び出す
        Then: ユーザーが正常に作成されること
        """

        # Given
        request = UserCreateRequest(
            name="Test User",
            username="testuser",
            email="test@example.com",
            password="hashed_password",
            description="Test description",
        )

        expected_user = User(
            id="test-user-id",
            name="Test User",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            description="Test description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        expected_guild = Guild(
            id="test-guild-id",
            owner_user_id="test-user-id",
        )

        expected_guild_member = GuildMember(
            id="test-guild-member-id",
            user_id="test-user-id",
            guild_id="test-guild-id",
        )

        # モックの設定
        mock_user_repository = AsyncMock()
        mock_user_repository.create_user.return_value = expected_user
        mock_user_repository_class.return_value = mock_user_repository

        mock_guild_repository = AsyncMock()
        mock_guild_repository.create_guild.return_value = expected_guild
        mock_guild_repository_class.return_value = mock_guild_repository

        mock_guild_member_repository = AsyncMock()
        mock_guild_member_repository.create_guild_member.return_value = expected_guild_member
        mock_guild_member_repository_class.return_value = mock_guild_member_repository

        # リポジトリをモックに置き換え
        self.use_case.user_repo = mock_user_repository
        self.use_case.guild_repo = mock_guild_repository
        self.use_case.guild_member_repo = mock_guild_member_repository

        # When
        result = await self.use_case.execute(self.mock_session, request)

        # Then
        self.assertIsInstance(result, UserResponse)
        self.assertEqual(result.id, str(expected_user.id))
        self.assertEqual(result.name, expected_user.name)
        self.assertEqual(result.username, expected_user.username)
        self.assertEqual(result.email, expected_user.email)
        self.assertEqual(result.description, expected_user.description)
        self.assertEqual(result.guild_id, str(expected_guild.id))

        mock_user_repository.create_user.assert_called_once()
        mock_guild_repository.create_guild.assert_called_once()

        # create_userに渡されたUserオブジェクトの検証
        call_args = mock_user_repository.create_user.call_args[0]
        # sessionの次の引数を取得
        created_user = call_args[1]
        # created_userからパスワードを取得
        created_password = created_user.password_hash
        # パスワードのソルトを取得
        salt_b64, _ = created_password.split("$")
        # ソルトとパスワードを用いて、ハッシュ化を再現
        recreated_hash = await hash_password(str(expected_user.password_hash), base64.b64decode(salt_b64))

        self.assertEqual(created_user.name, expected_user.name)
        self.assertEqual(created_user.username, expected_user.username)
        self.assertEqual(created_user.email, expected_user.email)
        self.assertEqual(created_user.description, expected_user.description)
        self.assertIsNone(created_user.id)
        # パスワードの検証
        self.assertIsNotNone(created_user.password_hash)
        self.assertNotEqual(created_user.password_hash, expected_user.password_hash)
        self.assertEqual(created_user.password_hash, recreated_hash)

    @patch("usecase.create_user.GuildMemberRepositoryIf")
    @patch("usecase.create_user.GuildRepositoryIf")
    @patch("usecase.create_user.UserRepositoryIf")
    async def test_execute_with_empty_description(
        self, mock_user_repository_class, mock_guild_repository_class, mock_guild_member_repository_class
    ):
        """
        Given: 説明が空のユーザー作成リクエスト
        When: executeメソッドを呼び出す
        Then: 説明が空でもユーザーが正常に作成されること
        """

        # Given
        request = UserCreateRequest(
            name="Test User",
            username="testuser",
            email="test@example.com",
            password="hashed_password",
            description="",
        )

        expected_user = User(
            id="test-user-id",
            name="Test User",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            description="",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        expected_guild = Guild(
            id="test-guild-id",
            owner_user_id="test-user-id",
        )

        expected_guild_member = GuildMember(
            id="test-guild-member-id",
            user_id="test-user-id",
            guild_id="test-guild-id",
        )

        # モックの設定
        mock_user_repository = AsyncMock()
        mock_user_repository.create_user.return_value = expected_user
        mock_user_repository_class.return_value = mock_user_repository

        mock_guild_repository = AsyncMock()
        mock_guild_repository.create_guild.return_value = expected_guild
        mock_guild_repository_class.return_value = mock_guild_repository

        mock_guild_member_repository = AsyncMock()
        mock_guild_member_repository.create_guild_member.return_value = expected_guild_member
        mock_guild_member_repository_class.return_value = mock_guild_member_repository

        # リポジトリをモックに置き換え
        self.use_case.user_repo = mock_user_repository
        self.use_case.guild_repo = mock_guild_repository
        self.use_case.guild_member_repo = mock_guild_member_repository

        # When
        result = await self.use_case.execute(self.mock_session, request)

        # Then
        self.assertIsInstance(result, UserResponse)
        self.assertEqual(result.id, str(expected_user.id))
        self.assertEqual(result.name, expected_user.name)
        self.assertEqual(result.username, expected_user.username)
        self.assertEqual(result.email, expected_user.email)
        self.assertEqual(result.description, expected_user.description)
        self.assertEqual(result.guild_id, str(expected_guild.id))

        mock_user_repository.create_user.assert_called_once()
        mock_guild_repository.create_guild.assert_called_once()

        # create_userに渡されたUserオブジェクトの検証
        call_args = mock_user_repository.create_user.call_args[0]
        # sessionの次の引数を取得
        created_user = call_args[1]
        # created_userからパスワードを取得
        created_password = created_user.password_hash
        # パスワードのソルトを取得
        salt_b64, _ = created_password.split("$")
        # ソルトとパスワードを用いて、ハッシュ化を再現
        recreated_hash = await hash_password(str(expected_user.password_hash), base64.b64decode(salt_b64))

        self.assertEqual(created_user.name, expected_user.name)
        self.assertEqual(created_user.username, expected_user.username)
        self.assertEqual(created_user.email, expected_user.email)
        self.assertIsNone(created_user.id)
        # パスワードの検証
        self.assertIsNotNone(created_user.password_hash)
        self.assertNotEqual(created_user.password_hash, expected_user.password_hash)
        self.assertEqual(created_user.password_hash, recreated_hash)

    @patch("usecase.create_user.GuildMemberRepositoryIf")
    @patch("usecase.create_user.GuildRepositoryIf")
    @patch("usecase.create_user.UserRepositoryIf")
    async def test_execute_repository_error(
        self, mock_user_repository_class, mock_guild_repository_class, mock_guild_member_repository_class
    ):
        """
        Given: リポジトリでエラーが発生する場合
        When: executeメソッドを呼び出す
        Then: エラーが適切に伝播されること
        """

        # Given
        request = UserCreateRequest(
            name="Test User",
            username="testuser",
            email="test@example.com",
            password="hashed_password",
            description="Test description",
        )

        # モックの設定
        mock_user_repository = AsyncMock()
        mock_user_repository.create_user.side_effect = Exception("データベースエラー")
        mock_user_repository_class.return_value = mock_user_repository

        mock_guild_repository = AsyncMock()
        mock_guild_repository_class.return_value = mock_guild_repository

        mock_guild_member_repository = AsyncMock()
        mock_guild_member_repository_class.return_value = mock_guild_member_repository

        # リポジトリをモックに置き換え
        self.use_case.user_repo = mock_user_repository
        self.use_case.guild_repo = mock_guild_repository
        self.use_case.guild_member_repo = mock_guild_member_repository

        # When & Then
        with self.assertRaises(Exception) as context:
            await self.use_case.execute(self.mock_session, request)

        self.assertEqual(str(context.exception), "データベースエラー")
        mock_user_repository.create_user.assert_called_once()
        # ユーザー作成でエラーが発生するため、ギルド作成は呼ばれない
        mock_guild_repository.create_guild.assert_not_called()

    @patch("usecase.create_user.GuildMemberRepositoryIf")
    @patch("usecase.create_user.GuildRepositoryIf")
    @patch("usecase.create_user.UserRepositoryIf")
    async def test_password_hashing_integration(
        self, mock_user_repository_class, mock_guild_repository_class, mock_guild_member_repository_class
    ):
        """
        Given: 同じパスワードを持つ複数のリクエスト
        When: executeメソッドを複数回呼び出す
        Then: 毎回異なるハッシュ値が生成されること（ソルト使用の確認）
        """

        # Given
        request1 = UserCreateRequest(
            name="Test User1",
            username="testuser1",
            email="test1@example.com",
            password="hashed_password",
            description="Test description",
        )

        request2 = UserCreateRequest(
            name="Test User2",
            username="testuser2",
            email="test2@example.com",
            password="hashed_password",
            description="Test description",
        )

        # モックの設定
        mock_user_repository = AsyncMock()
        mock_user_repository.create_user.return_value = User(
            id="test-user-id",
            name="Test User",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            description="Test description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_user_repository_class.return_value = mock_user_repository

        mock_guild_repository = AsyncMock()
        mock_guild_repository.create_guild.return_value = Guild(
            id="test-guild-id",
            owner_user_id="test-user-id",
        )
        mock_guild_repository_class.return_value = mock_guild_repository

        mock_guild_member_repository = AsyncMock()
        mock_guild_member_repository.create_guild_member.return_value = GuildMember(
            id="test-guild-member-id",
            user_id="test-user-id",
            guild_id="test-guild-id",
        )
        mock_guild_member_repository_class.return_value = mock_guild_member_repository

        # リポジトリをモックに置き換え
        self.use_case.user_repo = mock_user_repository
        self.use_case.guild_repo = mock_guild_repository
        self.use_case.guild_member_repo = mock_guild_member_repository

        # When
        await self.use_case.execute(self.mock_session, request1)
        await self.use_case.execute(self.mock_session, request2)

        # Then
        # 2回呼び出されることを確認
        self.assertEqual(mock_user_repository.create_user.call_count, 2)
        self.assertEqual(mock_guild_repository.create_guild.call_count, 2)
        self.assertEqual(mock_guild_member_repository.create_guild_member.call_count, 2)

        # 両方の呼び出しで渡されたUserオブジェクトのパスワードハッシュを取得
        first_call = mock_user_repository.create_user.call_args_list[0][0][1]
        second_call = mock_user_repository.create_user.call_args_list[1][0][1]

        # 同じパスワードでも異なるハッシュ値が生成されることを確認（ソルト使用）
        self.assertNotEqual(first_call.password_hash, second_call.password_hash)
        self.assertNotEqual(first_call.password_hash, str(request1.password))
        self.assertNotEqual(second_call.password_hash, str(request1.password))


if __name__ == "__main__":
    unittest.main()
