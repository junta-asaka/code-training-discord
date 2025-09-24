import os
import sys
import unittest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from injector import Injector
from sqlalchemy.ext.asyncio import AsyncSession

# テストファイルのルートディレクトリからの相対パスでsrcフォルダを指定
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from dependencies import configure
from domains import Message
from schema.message_schema import MessageCreateRequest, MessageResponse
from usecase.create_message import CreateMessageUseCaseIf


class TestCreateMessageUseCaseImpl(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # テスト用DIコンテナからユースケースを取得
        injector = Injector([configure])
        self.use_case = injector.get(CreateMessageUseCaseIf)
        self.mock_session = Mock(spec=AsyncSession)

    def create_mock_message(
        self,
        message_id=None,
        channel_id=None,
        user_id=None,
        message_type="default",
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

        message = Message(
            id=message_id,
            channel_id=channel_id,
            user_id=user_id,
            type=message_type,
            content=content,
            referenced_message_id=referenced_message_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        return message

    def create_mock_message_request(
        self, channel_id=None, user_id=None, message_type="default", content="Test message", referenced_message_id=None
    ):
        """モックのMessageCreateRequestオブジェクトを作成"""
        if channel_id is None:
            channel_id = uuid.uuid4()
        if user_id is None:
            user_id = uuid.uuid4()

        return MessageCreateRequest(
            channel_id=channel_id,
            user_id=user_id,
            type=message_type,
            content=content,
            referenced_message_id=referenced_message_id,
        )

    @patch("usecase.create_message.ChannelRepositoryIf")
    @patch("usecase.create_message.MessageRepositoryIf")
    async def test_execute_success(self, mock_message_repository_class, mock_channel_repository_class):
        """
        Given: 有効なメッセージ作成リクエスト
        When: executeメソッドを呼び出す
        Then: メッセージが正常に作成され、チャネルの最終メッセージIDが更新されること
        """

        # Given
        message_id = uuid.uuid4()
        channel_id = uuid.uuid4()
        user_id = uuid.uuid4()

        request = self.create_mock_message_request(
            channel_id=channel_id, user_id=user_id, message_type="default", content="Test message"
        )

        expected_message = self.create_mock_message(
            message_id=message_id,
            channel_id=channel_id,
            user_id=user_id,
            message_type="default",
            content="Test message",
        )

        # モックの設定
        mock_message_repo = AsyncMock()
        mock_message_repo.create_message.return_value = expected_message
        mock_message_repository_class.return_value = mock_message_repo

        mock_channel_repo = AsyncMock()
        mock_channel_repo.update_last_message_id.return_value = None
        mock_channel_repository_class.return_value = mock_channel_repo

        # リポジトリをモックに置き換え
        self.use_case.message_repo = mock_message_repo
        self.use_case.channel_repo = mock_channel_repo

        # When
        result = await self.use_case.execute(self.mock_session, request)

        # Then
        # メッセージが正常に作成されること
        self.assertIsInstance(result, MessageResponse)
        self.assertEqual(result.id, message_id)
        self.assertEqual(result.channel_id, channel_id)
        self.assertEqual(result.user_id, user_id)
        self.assertEqual(result.type, "default")
        self.assertEqual(result.content, "Test message")

        # メッセージリポジトリが呼び出されること
        mock_message_repo.create_message.assert_called_once()

        # チャネルの最終メッセージIDが更新されること
        mock_channel_repo.update_last_message_id.assert_called_once_with(
            self.mock_session, str(channel_id), str(message_id)
        )

    @patch("usecase.create_message.ChannelRepositoryIf")
    @patch("usecase.create_message.MessageRepositoryIf")
    async def test_execute_message_repository_error(self, mock_message_repository_class, mock_channel_repository_class):
        """
        Given: メッセージリポジトリでエラーが発生する状況
        When: executeメソッドを呼び出す
        Then: エラーが適切に伝播されること
        """

        # Given
        channel_id = uuid.uuid4()
        user_id = uuid.uuid4()

        request = self.create_mock_message_request(channel_id=channel_id, user_id=user_id)

        # モックの設定 - メッセージ作成でエラーを発生させる
        mock_message_repo = AsyncMock()
        mock_message_repo.create_message.side_effect = Exception("Database error")
        mock_message_repository_class.return_value = mock_message_repo

        mock_channel_repo = AsyncMock()
        mock_channel_repository_class.return_value = mock_channel_repo

        # リポジトリをモックに置き換え
        self.use_case.message_repo = mock_message_repo
        self.use_case.channel_repo = mock_channel_repo

        # When & Then
        with self.assertRaises(Exception) as context:
            await self.use_case.execute(self.mock_session, request)

        self.assertEqual(str(context.exception), "Database error")

        # メッセージリポジトリが呼び出されること
        mock_message_repo.create_message.assert_called_once()

        # エラー後にチャネル更新が呼び出されないこと
        mock_channel_repo.update_last_message_id.assert_not_called()

    @patch("usecase.create_message.ChannelRepositoryIf")
    @patch("usecase.create_message.MessageRepositoryIf")
    async def test_execute_channel_repository_error(self, mock_message_repository_class, mock_channel_repository_class):
        """
        Given: チャネルリポジトリでエラーが発生する状況
        When: executeメソッドを呼び出す
        Then: エラーが適切に伝播されること
        """

        # Given
        message_id = uuid.uuid4()
        channel_id = uuid.uuid4()
        user_id = uuid.uuid4()

        request = self.create_mock_message_request(channel_id=channel_id, user_id=user_id)

        expected_message = self.create_mock_message(message_id=message_id, channel_id=channel_id, user_id=user_id)

        # モックの設定 - チャネル更新でエラーを発生させる
        mock_message_repo = AsyncMock()
        mock_message_repo.create_message.return_value = expected_message
        mock_message_repository_class.return_value = mock_message_repo

        mock_channel_repo = AsyncMock()
        mock_channel_repo.update_last_message_id.side_effect = Exception("Channel update error")
        mock_channel_repository_class.return_value = mock_channel_repo

        # リポジトリをモックに置き換え
        self.use_case.message_repo = mock_message_repo
        self.use_case.channel_repo = mock_channel_repo

        # When & Then
        with self.assertRaises(Exception) as context:
            await self.use_case.execute(self.mock_session, request)

        self.assertEqual(str(context.exception), "Channel update error")

        # メッセージリポジトリが呼び出されること
        mock_message_repo.create_message.assert_called_once()

        # チャネル更新が呼び出されること
        mock_channel_repo.update_last_message_id.assert_called_once()


if __name__ == "__main__":
    unittest.main()
