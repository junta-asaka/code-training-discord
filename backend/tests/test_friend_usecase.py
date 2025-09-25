import os
import sys
import unittest
import uuid
from unittest.mock import AsyncMock, Mock, patch

from injector import Injector
from sqlalchemy.ext.asyncio import AsyncSession

# テストファイルのルートディレクトリからの相対パスでsrcフォルダを指定
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from dependencies import configure
from domains import Friend, User
from schema.friend_schema import FriendCreateRequest
from usecase.friend import FriendUseCaseIf


class TestFriendUseCaseImpl(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # テスト用DIコンテナからユースケースを取得
        injector = Injector([configure])
        self.use_case = injector.get(FriendUseCaseIf)
        self.mock_session = Mock(spec=AsyncSession)

    def create_mock_user(self, user_id=None, username="testuser", email="test@example.com"):
        """モックのUserオブジェクトを作成"""
        if user_id is None:
            user_id = uuid.uuid4()

        user = User(
            id=user_id,
            name="Test User",
            username=username,
            email=email,
            password_hash="hashed_password",
            description="Test description",
            created_at="2024-01-01T00:00:00Z",
        )
        return user

    def create_mock_friend(self, friend_id=None, user_id=None, related_user_id=None, friend_type="friend"):
        """モックのFriendオブジェクトを作成"""
        if friend_id is None:
            friend_id = uuid.uuid4()
        if user_id is None:
            user_id = uuid.uuid4()
        if related_user_id is None:
            related_user_id = uuid.uuid4()

        friend = Friend(id=friend_id, user_id=user_id, related_user_id=related_user_id, type=friend_type)
        # related_userのモック属性を追加
        friend.related_user = self.create_mock_user(user_id=related_user_id, username="relateduser")
        return friend

    def create_mock_friend_request(self, username="testuser", related_username="relateduser", friend_type="friend"):
        """モックのFriendCreateRequestオブジェクトを作成"""
        return FriendCreateRequest(username=username, related_username=related_username, type=friend_type)

    @patch("usecase.friend.GuildMemberRepositoryIf")
    @patch("usecase.friend.GuildRepositoryIf")
    @patch("usecase.friend.ChannelRepositoryIf")
    @patch("usecase.friend.UserRepositoryIf")
    @patch("usecase.friend.FriendRepositoryIf")
    async def test_create_friend_success(
        self,
        mock_friend_repository_class,
        mock_user_repository_class,
        mock_channel_repository_class,
        mock_guild_repository_class,
        mock_guild_member_repository_class,
    ):
        """
        Given: 有効なフレンド作成リクエスト
        When: create_friendメソッドを呼び出す
        Then: フレンドが正常に作成されること
        """

        # Given
        user_id = uuid.uuid4()
        related_user_id = uuid.uuid4()
        friend_id = uuid.uuid4()

        request = self.create_mock_friend_request()
        expected_user = self.create_mock_user(user_id=user_id, username="testuser")
        expected_related_user = self.create_mock_user(user_id=related_user_id, username="relateduser")
        expected_friend = self.create_mock_friend(friend_id=friend_id, user_id=user_id, related_user_id=related_user_id)

        # モックの設定
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_username.side_effect = [expected_user, expected_related_user]
        mock_user_repository_class.return_value = mock_user_repo

        mock_friend_repo = AsyncMock()
        mock_friend_repo.create_friend.return_value = expected_friend
        mock_friend_repository_class.return_value = mock_friend_repo

        mock_channel_repo = AsyncMock()
        mock_channel_repository_class.return_value = mock_channel_repo

        mock_guild_repo = AsyncMock()
        mock_guild_me = Mock(id=uuid.uuid4())
        mock_guild_related = Mock(id=uuid.uuid4())
        mock_guild_repo.get_guild_by_user_id_name.side_effect = [mock_guild_me, mock_guild_related]
        mock_guild_repo.create_guild.return_value = Mock(id=uuid.uuid4())
        mock_guild_repository_class.return_value = mock_guild_repo

        mock_guild_member_repo = AsyncMock()
        mock_guild_member_repository_class.return_value = mock_guild_member_repo

        self.use_case.user_repo = mock_user_repo
        self.use_case.friend_repo = mock_friend_repo
        self.use_case.channel_repo = mock_channel_repo
        self.use_case.guild_repo = mock_guild_repo
        self.use_case.guild_member_repo = mock_guild_member_repo

        # When
        result = await self.use_case.create_friend(self.mock_session, request)

        # Then
        self.assertIsNotNone(result)
        if result is not None:
            self.assertEqual(result.id, expected_friend.id)
            self.assertEqual(result.user_id, user_id)
            self.assertEqual(result.related_user_id, related_user_id)
            self.assertEqual(result.type, "friend")

        # get_user_by_usernameが2回呼ばれることを確認（自ユーザーと相手ユーザー）
        self.assertEqual(mock_user_repo.get_user_by_username.call_count, 2)
        mock_user_repo.get_user_by_username.assert_any_call(self.mock_session, "testuser")
        mock_user_repo.get_user_by_username.assert_any_call(self.mock_session, "relateduser")

        # create_friendが1回呼ばれることを確認
        mock_friend_repo.create_friend.assert_called_once()

        # create_friendに渡されたFriendオブジェクトの検証
        call_args = mock_friend_repo.create_friend.call_args[0]
        created_friend = call_args[1]
        self.assertEqual(created_friend.user_id, user_id)
        self.assertEqual(created_friend.related_user_id, related_user_id)
        self.assertEqual(created_friend.type, "friend")

    @patch("usecase.friend.GuildMemberRepositoryIf")
    @patch("usecase.friend.GuildRepositoryIf")
    @patch("usecase.friend.ChannelRepositoryIf")
    @patch("usecase.friend.UserRepositoryIf")
    @patch("usecase.friend.FriendRepositoryIf")
    async def test_create_friend_user_not_found(
        self,
        mock_friend_repository_class,
        mock_user_repository_class,
        mock_channel_repository_class,
        mock_guild_repository_class,
        mock_guild_member_repository_class,
    ):
        """
        Given: 存在しない自ユーザー名を含むフレンド作成リクエスト
        When: create_friendメソッドを呼び出す
        Then: Noneが返されること
        """

        # Given
        request = self.create_mock_friend_request(username="nonexistuser")

        # モックの設定
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_username.return_value = None  # ユーザーが見つからない
        mock_user_repository_class.return_value = mock_user_repo

        mock_friend_repo = AsyncMock()
        mock_friend_repository_class.return_value = mock_friend_repo

        mock_channel_repo = AsyncMock()
        mock_channel_repository_class.return_value = mock_channel_repo

        mock_guild_repo = AsyncMock()
        mock_guild_repository_class.return_value = mock_guild_repo

        mock_guild_member_repo = AsyncMock()
        mock_guild_member_repository_class.return_value = mock_guild_member_repo

        self.use_case.user_repo = mock_user_repo
        self.use_case.friend_repo = mock_friend_repo
        self.use_case.channel_repo = mock_channel_repo
        self.use_case.guild_repo = mock_guild_repo
        self.use_case.guild_member_repo = mock_guild_member_repo

        # When
        result = await self.use_case.create_friend(self.mock_session, request)

        # Then
        self.assertIsNone(result)
        mock_user_repo.get_user_by_username.assert_called_once_with(self.mock_session, "nonexistuser")
        mock_friend_repo.create_friend.assert_not_called()

    @patch("usecase.friend.GuildMemberRepositoryIf")
    @patch("usecase.friend.GuildRepositoryIf")
    @patch("usecase.friend.ChannelRepositoryIf")
    @patch("usecase.friend.UserRepositoryIf")
    @patch("usecase.friend.FriendRepositoryIf")
    async def test_create_friend_related_user_not_found(
        self,
        mock_friend_repository_class,
        mock_user_repository_class,
        mock_channel_repository_class,
        mock_guild_repository_class,
        mock_guild_member_repository_class,
    ):
        """
        Given: 存在しない相手ユーザー名を含むフレンド作成リクエスト
        When: create_friendメソッドを呼び出す
        Then: Noneが返されること
        """

        # Given
        user_id = uuid.uuid4()
        request = self.create_mock_friend_request(related_username="nonexistuser")
        expected_user = self.create_mock_user(user_id=user_id, username="testuser")

        # モックの設定
        mock_user_repo = AsyncMock()
        # 最初の呼び出しでは自ユーザーを返し、2回目の呼び出しでは相手ユーザーがNone
        mock_user_repo.get_user_by_username.side_effect = [expected_user, None]
        mock_user_repository_class.return_value = mock_user_repo

        mock_friend_repo = AsyncMock()
        mock_friend_repository_class.return_value = mock_friend_repo

        mock_channel_repo = AsyncMock()
        mock_channel_repository_class.return_value = mock_channel_repo

        mock_guild_repo = AsyncMock()
        mock_guild_repository_class.return_value = mock_guild_repo

        mock_guild_member_repo = AsyncMock()
        mock_guild_member_repository_class.return_value = mock_guild_member_repo

        self.use_case.user_repo = mock_user_repo
        self.use_case.friend_repo = mock_friend_repo
        self.use_case.channel_repo = mock_channel_repo
        self.use_case.guild_repo = mock_guild_repo
        self.use_case.guild_member_repo = mock_guild_member_repo

        # When
        result = await self.use_case.create_friend(self.mock_session, request)

        # Then
        self.assertIsNone(result)
        self.assertEqual(mock_user_repo.get_user_by_username.call_count, 2)
        mock_user_repo.get_user_by_username.assert_any_call(self.mock_session, "testuser")
        mock_user_repo.get_user_by_username.assert_any_call(self.mock_session, "nonexistuser")
        mock_friend_repo.create_friend.assert_not_called()

    @patch("usecase.friend.ChannelRepositoryIf")
    @patch("usecase.friend.UserRepositoryIf")
    @patch("usecase.friend.FriendRepositoryIf")
    async def test_get_friend_all_success(
        self, mock_friend_repository_class, mock_user_repository_class, mock_channel_repository_class
    ):
        """
        Given: 有効なユーザーIDとフレンドが存在する場合
        When: get_friend_allメソッドを呼び出す
        Then: フレンドのレスポンスリストが返されること
        """

        # Given
        user_id = str(uuid.uuid4())
        friend1_id = uuid.uuid4()
        friend2_id = uuid.uuid4()
        related_user1_id = uuid.uuid4()
        related_user2_id = uuid.uuid4()
        channel1_id = uuid.uuid4()
        channel2_id = uuid.uuid4()

        # フレンドのモック
        friend1 = self.create_mock_friend(friend_id=friend1_id, user_id=user_id, related_user_id=related_user1_id)
        friend2 = self.create_mock_friend(friend_id=friend2_id, user_id=user_id, related_user_id=related_user2_id)
        friends = [friend1, friend2]

        # 相手ユーザーのモック
        related_user1 = self.create_mock_user(user_id=related_user1_id, username="friend1")
        related_user2 = self.create_mock_user(user_id=related_user2_id, username="friend2")
        related_users = [related_user1, related_user2]

        # チャネルのモック
        mock_channel1 = Mock(id=channel1_id)
        mock_channel2 = Mock(id=channel2_id)

        # モックの設定
        mock_friend_repo = AsyncMock()
        mock_friend_repo.get_friend_all.return_value = friends
        mock_friend_repository_class.return_value = mock_friend_repo

        mock_user_repo = AsyncMock()
        mock_user_repo.get_users_by_id.return_value = related_users
        mock_user_repository_class.return_value = mock_user_repo

        mock_channel_repo = AsyncMock()
        mock_channel_repo.get_channels_by_user_ids_type_name.side_effect = [mock_channel1, mock_channel2]
        mock_channel_repository_class.return_value = mock_channel_repo

        self.use_case.friend_repo = mock_friend_repo
        self.use_case.user_repo = mock_user_repo
        self.use_case.channel_repo = mock_channel_repo

        # When
        result = await self.use_case.get_friend_all(self.mock_session, user_id)

        # Then
        self.assertIsNotNone(result)
        if result is not None:
            self.assertEqual(len(result), 2)
            # FriendGetResponseオブジェクトの属性をチェック
            self.assertEqual(result[0].username, "friend1")
            self.assertEqual(result[0].channel_id, channel1_id)
            self.assertEqual(result[1].username, "friend2")
            self.assertEqual(result[1].channel_id, channel2_id)

        mock_friend_repo.get_friend_all.assert_called_once_with(self.mock_session, user_id)
        mock_user_repo.get_users_by_id.assert_called_once_with(
            self.mock_session, [str(related_user1_id), str(related_user2_id)]
        )
        # チャネル取得が2回呼ばれることを確認
        self.assertEqual(mock_channel_repo.get_channels_by_user_ids_type_name.call_count, 2)

    @patch("usecase.friend.ChannelRepositoryIf")
    @patch("usecase.friend.UserRepositoryIf")
    @patch("usecase.friend.FriendRepositoryIf")
    async def test_get_friend_all_empty_list(
        self, mock_friend_repository_class, mock_user_repository_class, mock_channel_repository_class
    ):
        """
        Given: フレンドが存在しないユーザーID
        When: get_friend_allメソッドを呼び出す
        Then: 空のリストが返されること
        """

        # Given
        user_id = str(uuid.uuid4())

        # モックの設定
        mock_friend_repo = AsyncMock()
        mock_friend_repo.get_friend_all.return_value = []  # フレンドが0件
        mock_friend_repository_class.return_value = mock_friend_repo

        mock_user_repo = AsyncMock()
        mock_user_repo.get_users_by_id.return_value = []  # 空のユーザーリスト
        mock_user_repository_class.return_value = mock_user_repo

        mock_channel_repo = AsyncMock()
        mock_channel_repository_class.return_value = mock_channel_repo

        self.use_case.friend_repo = mock_friend_repo
        self.use_case.user_repo = mock_user_repo
        self.use_case.channel_repo = mock_channel_repo

        # When
        result = await self.use_case.get_friend_all(self.mock_session, user_id)

        # Then
        self.assertIsNotNone(result)
        if result is not None:
            self.assertEqual(len(result), 0)

        mock_friend_repo.get_friend_all.assert_called_once_with(self.mock_session, user_id)
        mock_user_repo.get_users_by_id.assert_called_once_with(self.mock_session, [])

    @patch("usecase.friend.GuildMemberRepositoryIf")
    @patch("usecase.friend.GuildRepositoryIf")
    @patch("usecase.friend.ChannelRepositoryIf")
    @patch("usecase.friend.UserRepositoryIf")
    @patch("usecase.friend.FriendRepositoryIf")
    async def test_create_friend_repository_error(
        self,
        mock_friend_repository_class,
        mock_user_repository_class,
        mock_channel_repository_class,
        mock_guild_repository_class,
        mock_guild_member_repository_class,
    ):
        """
        Given: リポジトリでエラーが発生する場合
        When: create_friendメソッドを呼び出す
        Then: エラーが適切に伝播されること
        """

        # Given
        user_id = uuid.uuid4()
        related_user_id = uuid.uuid4()

        request = self.create_mock_friend_request()
        expected_user = self.create_mock_user(user_id=user_id, username="testuser")
        expected_related_user = self.create_mock_user(user_id=related_user_id, username="relateduser")

        # モックの設定
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_username.side_effect = [expected_user, expected_related_user]
        mock_user_repository_class.return_value = mock_user_repo

        mock_friend_repo = AsyncMock()
        mock_friend_repo.create_friend.side_effect = Exception("データベースエラー")
        mock_friend_repository_class.return_value = mock_friend_repo

        mock_channel_repo = AsyncMock()
        mock_channel_repository_class.return_value = mock_channel_repo

        mock_guild_repo = AsyncMock()
        mock_guild_me = Mock(id=uuid.uuid4())
        mock_guild_related = Mock(id=uuid.uuid4())
        mock_guild_repo.get_guild_by_user_id_name.side_effect = [mock_guild_me, mock_guild_related]
        mock_guild_repo.create_guild.return_value = Mock(id=uuid.uuid4())
        mock_guild_repository_class.return_value = mock_guild_repo

        mock_guild_member_repo = AsyncMock()
        mock_guild_member_repository_class.return_value = mock_guild_member_repo

        self.use_case.user_repo = mock_user_repo
        self.use_case.friend_repo = mock_friend_repo
        self.use_case.channel_repo = mock_channel_repo
        self.use_case.guild_repo = mock_guild_repo
        self.use_case.guild_member_repo = mock_guild_member_repo

        # When & Then
        with self.assertRaises(Exception) as context:
            await self.use_case.create_friend(self.mock_session, request)

        self.assertEqual(str(context.exception), "データベースエラー")
        mock_friend_repo.create_friend.assert_called_once()

    @patch("usecase.friend.ChannelRepositoryIf")
    @patch("usecase.friend.UserRepositoryIf")
    @patch("usecase.friend.FriendRepositoryIf")
    async def test_get_friend_all_repository_error(
        self, mock_friend_repository_class, mock_user_repository_class, mock_channel_repository_class
    ):
        """
        Given: フレンドリポジトリでエラーが発生する場合
        When: get_friend_allメソッドを呼び出す
        Then: エラーが適切に伝播されること
        """

        # Given
        user_id = str(uuid.uuid4())

        # モックの設定
        mock_friend_repo = AsyncMock()
        mock_friend_repo.get_friend_all.side_effect = Exception("フレンド取得エラー")
        mock_friend_repository_class.return_value = mock_friend_repo

        mock_user_repo = AsyncMock()
        mock_user_repository_class.return_value = mock_user_repo

        mock_channel_repo = AsyncMock()
        mock_channel_repository_class.return_value = mock_channel_repo

        self.use_case.friend_repo = mock_friend_repo
        self.use_case.user_repo = mock_user_repo
        self.use_case.channel_repo = mock_channel_repo

        # When & Then
        with self.assertRaises(Exception) as context:
            await self.use_case.get_friend_all(self.mock_session, user_id)

        self.assertEqual(str(context.exception), "フレンド取得エラー")
        mock_friend_repo.get_friend_all.assert_called_once_with(self.mock_session, user_id)


if __name__ == "__main__":
    unittest.main()
