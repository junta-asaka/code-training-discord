import os
import sys
import unittest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from injector import Injector
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.friend import CHANNEL_TYPE_TEXT

# テストファイルのルートディレクトリからの相対パスでsrcフォルダを指定
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from dependencies import configure
from domains import Channel
from schema.channel_schema import ChannelGetResponse
from usecase.get_channel_messages import (
    GetChannelMessagesUseCaseIf,
    GetChannelMessageTransactionError,
)


class TestChannelUseCaseImpl(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # テスト用DIコンテナからユースケースを取得
        injector = Injector([configure])
        self.use_case = injector.get(GetChannelMessagesUseCaseIf)
        self.mock_session = Mock(spec=AsyncSession)

    def create_mock_channel(self, channel_id=None, guild_id=None, name="test-channel"):
        """モックのChannelオブジェクトを作成"""
        if channel_id is None:
            channel_id = uuid.uuid4()
        if guild_id is None:
            guild_id = uuid.uuid4()

        channel = Channel(
            id=channel_id,
            guild_id=guild_id,
            type=CHANNEL_TYPE_TEXT,
            name=name,
            owner_user_id=uuid.uuid4(),
            last_message_id=None,
            deleted_at=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        return channel

    def create_mock_message(
        self,
        message_id=None,
        channel_id=None,
        user_id=None,
        content="Test message",
        referenced_message_id=None,
    ):
        """モックのMessageオブジェクトを作成"""
        if message_id is None:
            message_id = uuid.uuid4()
        if channel_id is None:
            channel_id = uuid.uuid4()
        if user_id is None:
            user_id = uuid.uuid4()

        # MessageResponseスキーマに合うようにフィールドを設定
        message = Mock()
        message.id = message_id
        message.channel_id = channel_id
        message.user_id = user_id  # MessageResponseスキーマではuser_id
        message.type = "default"
        message.content = content
        message.referenced_message_id = referenced_message_id
        message.created_at = "2023-01-01T00:00:00Z"
        message.updated_at = "2023-01-01T00:00:00Z"

        return message

    @patch("usecase.get_channel_messages.ChannelRepositoryIf")
    @patch("usecase.get_channel_messages.MessageRepositoryIf")
    async def test_execute_success_with_messages(
        self, mock_message_repository_class, mock_channel_repository_class
    ):
        """
        Given: 有効なチャネルIDとメッセージが存在する
        When: executeメソッドを呼び出す
        Then: チャネル情報とメッセージ一覧が正常に返却されること
        """

        # Given
        test_channel_id = str(uuid.uuid4())
        test_guild_id = uuid.uuid4()
        test_user_id = uuid.uuid4()

        expected_channel = self.create_mock_channel(
            channel_id=uuid.UUID(test_channel_id),
            guild_id=test_guild_id,
            name="general",
        )

        expected_messages = [
            self.create_mock_message(
                channel_id=uuid.UUID(test_channel_id),
                user_id=test_user_id,
                content="Hello, world!",
            ),
            self.create_mock_message(
                channel_id=uuid.UUID(test_channel_id),
                user_id=test_user_id,
                content="How are you?",
            ),
        ]

        # モックの設定
        mock_channel_repo = AsyncMock()
        mock_channel_repo.get_channel_by_id.return_value = expected_channel
        mock_channel_repository_class.return_value = mock_channel_repo

        mock_message_repo = AsyncMock()
        mock_message_repo.get_message_by_channel_id.return_value = expected_messages
        mock_message_repository_class.return_value = mock_message_repo

        self.use_case.channel_repo = mock_channel_repo
        self.use_case.message_repo = mock_message_repo

        # When
        result = await self.use_case.execute(self.mock_session, test_channel_id)

        # Then
        self.assertIsInstance(result, ChannelGetResponse)
        self.assertEqual(str(result.id), test_channel_id)
        self.assertEqual(result.guild_id, test_guild_id)
        self.assertEqual(result.name, "general")
        self.assertEqual(len(result.messages), 2)
        self.assertEqual(result.messages[0].content, "Hello, world!")
        self.assertEqual(result.messages[1].content, "How are you?")

        # モックメソッドの呼び出し確認
        mock_channel_repo.get_channel_by_id.assert_called_once_with(
            self.mock_session, test_channel_id
        )
        mock_message_repo.get_message_by_channel_id.assert_called_once_with(
            self.mock_session, test_channel_id
        )

    @patch("usecase.get_channel_messages.ChannelRepositoryIf")
    @patch("usecase.get_channel_messages.MessageRepositoryIf")
    async def test_execute_success_with_empty_messages(
        self, mock_message_repository_class, mock_channel_repository_class
    ):
        """
        Given: 有効なチャネルIDだがメッセージが存在しない
        When: executeメソッドを呼び出す
        Then: チャネル情報と空のメッセージ一覧が返却されること
        """

        # Given
        test_channel_id = str(uuid.uuid4())
        test_guild_id = uuid.uuid4()

        expected_channel = self.create_mock_channel(
            channel_id=uuid.UUID(test_channel_id),
            guild_id=test_guild_id,
            name="empty-channel",
        )

        expected_messages = []  # 空のメッセージリスト

        # モックの設定
        mock_channel_repo = AsyncMock()
        mock_channel_repo.get_channel_by_id.return_value = expected_channel
        mock_channel_repository_class.return_value = mock_channel_repo

        mock_message_repo = AsyncMock()
        mock_message_repo.get_message_by_channel_id.return_value = expected_messages
        mock_message_repository_class.return_value = mock_message_repo

        self.use_case.channel_repo = mock_channel_repo
        self.use_case.message_repo = mock_message_repo

        # When
        result = await self.use_case.execute(self.mock_session, test_channel_id)

        # Then
        self.assertIsInstance(result, ChannelGetResponse)
        self.assertEqual(str(result.id), test_channel_id)
        self.assertEqual(result.guild_id, test_guild_id)
        self.assertEqual(result.name, "empty-channel")
        self.assertEqual(len(result.messages), 0)

        # モックメソッドの呼び出し確認
        mock_channel_repo.get_channel_by_id.assert_called_once_with(
            self.mock_session, test_channel_id
        )
        mock_message_repo.get_message_by_channel_id.assert_called_once_with(
            self.mock_session, test_channel_id
        )

    @patch("usecase.get_channel_messages.ChannelRepositoryIf")
    @patch("usecase.get_channel_messages.MessageRepositoryIf")
    async def test_execute_channel_not_found(
        self, mock_message_repository_class, mock_channel_repository_class
    ):
        """
        Given: 存在しないチャネルID
        When: executeメソッドを呼び出す
        Then: チャネルリポジトリから例外が発生すること
        """

        # Given
        test_channel_id = str(uuid.uuid4())

        # モックの設定
        mock_channel_repo = AsyncMock()
        mock_channel_repo.get_channel_by_id.side_effect = Exception("Channel not found")
        mock_channel_repository_class.return_value = mock_channel_repo

        mock_message_repo = AsyncMock()
        mock_message_repository_class.return_value = mock_message_repo

        self.use_case.channel_repo = mock_channel_repo
        self.use_case.message_repo = mock_message_repo

        # When & Then
        with self.assertRaises(GetChannelMessageTransactionError) as context:
            await self.use_case.execute(self.mock_session, test_channel_id)

        self.assertEqual(str(context.exception), "予期しないエラーが発生しました")

        # モックメソッドの呼び出し確認
        mock_channel_repo.get_channel_by_id.assert_called_once_with(
            self.mock_session, test_channel_id
        )
        # チャネル取得でエラーが発生した場合、メッセージ取得は呼ばれない
        mock_message_repo.get_message_by_channel_id.assert_not_called()

    @patch("usecase.get_channel_messages.ChannelRepositoryIf")
    @patch("usecase.get_channel_messages.MessageRepositoryIf")
    async def test_execute_message_repository_error(
        self, mock_message_repository_class, mock_channel_repository_class
    ):
        """
        Given: 有効なチャネルIDだがメッセージ取得でエラーが発生
        When: executeメソッドを呼び出す
        Then: メッセージリポジトリから例外が発生すること
        """

        # Given
        test_channel_id = str(uuid.uuid4())
        test_guild_id = uuid.uuid4()

        expected_channel = self.create_mock_channel(
            channel_id=uuid.UUID(test_channel_id),
            guild_id=test_guild_id,
            name="error-channel",
        )

        # モックの設定
        mock_channel_repo = AsyncMock()
        mock_channel_repo.get_channel_by_id.return_value = expected_channel
        mock_channel_repository_class.return_value = mock_channel_repo

        mock_message_repo = AsyncMock()
        mock_message_repo.get_message_by_channel_id.side_effect = Exception(
            "Database connection error"
        )
        mock_message_repository_class.return_value = mock_message_repo

        self.use_case.channel_repo = mock_channel_repo
        self.use_case.message_repo = mock_message_repo

        # When & Then
        with self.assertRaises(GetChannelMessageTransactionError) as context:
            await self.use_case.execute(self.mock_session, test_channel_id)

        self.assertEqual(str(context.exception), "予期しないエラーが発生しました")

        # モックメソッドの呼び出し確認
        mock_channel_repo.get_channel_by_id.assert_called_once_with(
            self.mock_session, test_channel_id
        )
        mock_message_repo.get_message_by_channel_id.assert_called_once_with(
            self.mock_session, test_channel_id
        )


if __name__ == "__main__":
    unittest.main()
