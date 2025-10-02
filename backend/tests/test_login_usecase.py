import os
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from injector import Injector
from sqlalchemy.ext.asyncio import AsyncSession

# テストファイルのルートディレクトリからの相対パスでsrcフォルダを指定
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from dependencies import configure
from domains import Session, User
from usecase.login import LoginUseCaseIf


class TestLoginUseCaseImpl(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # テスト用DIコンテナからユースケースを取得
        injector = Injector([configure])
        self.use_case = injector.get(LoginUseCaseIf)
        self.mock_session = Mock(spec=AsyncSession)

    def create_mock_request(self, user_agent="TestAgent", client_host="127.0.0.1", cookies=None, headers=None):
        """モックのRequestオブジェクトを作成"""
        request = Mock(spec=Request)
        request.headers = Mock()
        request.headers.get = Mock(
            side_effect=lambda key, default=None: {
                "User-Agent": user_agent,
                "Authorization": headers.get("Authorization", "") if headers else "",
            }.get(key, default)
        )
        request.client = Mock()
        request.client.host = client_host
        request.cookies = Mock()
        request.cookies.get = Mock(side_effect=lambda key: cookies.get(key) if cookies else None)

        return request

    def create_mock_form_data(self, username="testuser", password="testpass"):
        """モックのOAuth2PasswordRequestFormオブジェクトを作成"""
        form_data = Mock(spec=OAuth2PasswordRequestForm)
        form_data.username = username
        form_data.password = password

        return form_data

    @patch("usecase.login.UserRepositoryIf")
    @patch("usecase.login.SessionRepositoryIf")
    @patch("usecase.login.verify_password")
    async def test_create_session_success(
        self, mock_verify_password, mock_session_repository_class, mock_user_repository_class
    ):
        """
        Given: 有効なユーザー認証情報
        When: create_sessionメソッドを呼び出す
        Then: セッションが正常に作成されること
        """

        # Given
        expected_user = User(id=1, username="testuser", email="test@example.com", password_hash="hashed_password")
        expected_session = Session(
            id=1, user_id=1, refresh_token_hash="test_token", user_agent="TestAgent", ip_address="127.0.0.1"
        )

        form_data = self.create_mock_form_data()
        request = self.create_mock_request()

        # モックの設定
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_username.return_value = expected_user
        mock_user_repository_class.return_value = mock_user_repo

        mock_session_repo = AsyncMock()
        mock_session_repo.create_session.return_value = expected_session
        mock_session_repository_class.return_value = mock_session_repo

        mock_verify_password.return_value = True

        self.use_case.user_repo = mock_user_repo
        self.use_case.session_repo = mock_session_repo

        # When
        result = await self.use_case.create_session(self.mock_session, request, form_data)

        # Then
        self.assertIsNotNone(result["session"])
        self.assertEqual(result["session"].id, expected_session.id)
        self.assertEqual(result["user"], expected_user)
        # assert_called_once_with: 指定した引数で1回呼ばれたかどうかを確認
        mock_user_repo.get_user_by_username.assert_called_once_with(self.mock_session, "testuser")
        mock_verify_password.assert_called_once_with("hashed_password", "testpass")
        # assert_called_once: 引数に関係なく1回呼ばれたかどうかを確認
        mock_session_repo.create_session.assert_called_once()

    @patch("usecase.login.UserRepositoryIf")
    @patch("usecase.login.SessionRepositoryIf")
    @patch("usecase.login.verify_password")
    async def test_create_session_invalid_user(
        self, mock_verify_password, mock_session_repository_class, mock_user_repository_class
    ):
        """
        Given: 存在しないユーザー名
        When: create_sessionメソッドを呼び出す
        Then: セッションがNoneで返されること
        """

        # Given
        form_data = self.create_mock_form_data(username="nonexist")
        request = self.create_mock_request()

        # モックの設定
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_username.return_value = None
        mock_user_repository_class.return_value = mock_user_repo

        mock_session_repo = AsyncMock()
        mock_session_repository_class.return_value = mock_session_repo

        self.use_case.user_repo = mock_user_repo
        self.use_case.session_repo = mock_session_repo

        # When
        result = await self.use_case.create_session(self.mock_session, request, form_data)

        # Then
        self.assertIsNone(result["session"])
        self.assertIsNone(result["user"])
        mock_user_repo.get_user_by_username.assert_called_once_with(self.mock_session, "nonexist")
        mock_verify_password.assert_not_called()

    @patch("usecase.login.UserRepositoryIf")
    @patch("usecase.login.SessionRepositoryIf")
    @patch("usecase.login.verify_password")
    async def test_create_session_invalid_password(
        self, mock_verify_password, mock_session_repository_class, mock_user_repository_class
    ):
        """
        Given: 有効なユーザー名だが無効なパスワード
        When: create_sessionメソッドを呼び出す
        Then: セッションがNoneで返されること
        """

        # Given
        expected_user = User(id=1, username="testuser", email="test@example.com", password_hash="hashed_password")
        form_data = self.create_mock_form_data(password="wrong_password")
        request = self.create_mock_request()

        # モックの設定
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_username.return_value = expected_user
        mock_user_repository_class.return_value = mock_user_repo

        mock_session_repo = AsyncMock()
        mock_session_repository_class.return_value = mock_session_repo

        mock_verify_password.return_value = False

        self.use_case.user_repo = mock_user_repo
        self.use_case.session_repo = mock_session_repo

        # When
        result = await self.use_case.create_session(self.mock_session, request, form_data)

        # Then
        self.assertIsNone(result["session"])
        self.assertEqual(result["user"], expected_user)
        mock_user_repo.get_user_by_username.assert_called_once_with(self.mock_session, "testuser")
        mock_verify_password.assert_called_once_with("hashed_password", "wrong_password")

    @patch("usecase.login.UserRepositoryIf")
    @patch("usecase.login.SessionRepositoryIf")
    @patch("usecase.login.verify_password")
    @patch("usecase.login.create_access_token")
    async def test_create_session_with_no_client(
        self, mock_create_access_token, mock_verify_password, mock_session_repository_class, mock_user_repository_class
    ):
        """
        Given: 有効な認証情報だがclientが存在しないリクエスト
        When: create_sessionメソッドを呼び出す
        Then: ip_addressがNoneでセッションが作成されること
        """

        # Given
        expected_user = User(id=1, username="testuser", email="test@example.com", password_hash="hashed_password")
        expected_session = Session(
            id=1, user_id=1, refresh_token_hash="test_token", user_agent="TestAgent", ip_address=None
        )

        form_data = self.create_mock_form_data()
        request = Mock(spec=Request)
        request.headers = Mock()
        request.headers.get = Mock(return_value="TestAgent")
        request.client = None  # clientがNone

        # モックの設定
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_username.return_value = expected_user
        mock_user_repository_class.return_value = mock_user_repo

        mock_session_repo = AsyncMock()
        mock_session_repo.create_session.return_value = expected_session
        mock_session_repository_class.return_value = mock_session_repo

        mock_verify_password.return_value = True
        mock_create_access_token.return_value = "test_token"

        self.use_case.user_repo = mock_user_repo
        self.use_case.session_repo = mock_session_repo

        # When
        result = await self.use_case.create_session(self.mock_session, request, form_data)

        # Then
        self.assertIsNotNone(result["session"])
        self.assertEqual(result["session"].ip_address, None)
        self.assertEqual(result["user"], expected_user)

    @patch("usecase.login.UserRepositoryIf")
    @patch("usecase.login.SessionRepositoryIf")
    async def test_auth_session_success_with_cookie(self, mock_session_repository_class, mock_user_repository_class):
        """
        Given: 有効なセッショントークンをCookieに含むリクエスト
        When: auth_sessionメソッドを呼び出す
        Then: ユーザー情報が返されること
        """

        # Given
        expected_session = Session(
            id=1, user_id=1, refresh_token_hash="test_token", user_agent="TestAgent", ip_address="127.0.0.1"
        )
        expected_user = User(id=1, username="testuser", email="test@example.com", password_hash="hashed_password")

        request = self.create_mock_request(cookies={"session_token": "test_token"})

        # モックの設定
        mock_session_repo = AsyncMock()
        mock_session_repo.get_session_by_token.return_value = expected_session
        mock_session_repository_class.return_value = mock_session_repo

        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_id.return_value = expected_user
        mock_user_repository_class.return_value = mock_user_repo

        self.use_case.session_repo = mock_session_repo
        self.use_case.user_repo = mock_user_repo

        # When
        result = await self.use_case.auth_session(self.mock_session, request)

        # Then
        self.assertEqual(result, expected_user)
        mock_session_repo.get_session_by_token.assert_called_once_with(self.mock_session, "test_token")
        mock_user_repo.get_user_by_id.assert_called_once_with(self.mock_session, "1")

    @patch("usecase.login.UserRepositoryIf")
    @patch("usecase.login.SessionRepositoryIf")
    async def test_auth_session_success_with_authorization_header(
        self, mock_session_repository_class, mock_user_repository_class
    ):
        """
        Given: 有効なセッショントークンをAuthorizationヘッダーに含むリクエスト
        When: auth_sessionメソッドを呼び出す
        Then: ユーザー情報が返されること
        """

        # Given
        expected_session = Session(
            id=1, user_id=1, refresh_token_hash="test_token", user_agent="TestAgent", ip_address="127.0.0.1"
        )
        expected_user = User(id=1, username="testuser", email="test@example.com", password_hash="hashed_password")

        request = self.create_mock_request(headers={"Authorization": "Bearer test_token"})

        # モックの設定
        mock_session_repo = AsyncMock()
        mock_session_repo.get_session_by_token.return_value = expected_session
        mock_session_repository_class.return_value = mock_session_repo

        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_id.return_value = expected_user
        mock_user_repository_class.return_value = mock_user_repo

        self.use_case.session_repo = mock_session_repo
        self.use_case.user_repo = mock_user_repo

        # When
        result = await self.use_case.auth_session(self.mock_session, request)

        # Then
        self.assertEqual(result, expected_user)
        mock_session_repo.get_session_by_token.assert_called_once_with(self.mock_session, "test_token")
        mock_user_repo.get_user_by_id.assert_called_once_with(self.mock_session, "1")

    @patch("usecase.login.UserRepositoryIf")
    @patch("usecase.login.SessionRepositoryIf")
    async def test_auth_session_cookie_priority_over_header(
        self, mock_session_repository_class, mock_user_repository_class
    ):
        """
        Given: CookieとAuthorizationヘッダーの両方にトークンが含まれるリクエスト
        When: auth_sessionメソッドを呼び出す
        Then: Cookieのトークンが優先されること
        """

        # Given
        expected_session = Session(
            id=1, user_id=1, refresh_token_hash="cookie_token", user_agent="TestAgent", ip_address="127.0.0.1"
        )
        expected_user = User(id=1, username="testuser", email="test@example.com", password_hash="hashed_password")

        request = self.create_mock_request(
            cookies={"session_token": "cookie_token"}, headers={"Authorization": "Bearer header_token"}
        )

        # モックの設定
        mock_session_repo = AsyncMock()
        mock_session_repo.get_session_by_token.return_value = expected_session
        mock_session_repository_class.return_value = mock_session_repo

        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_id.return_value = expected_user
        mock_user_repository_class.return_value = mock_user_repo

        self.use_case.session_repo = mock_session_repo
        self.use_case.user_repo = mock_user_repo

        # When
        result = await self.use_case.auth_session(self.mock_session, request)

        # Then
        self.assertEqual(result, expected_user)
        mock_session_repo.get_session_by_token.assert_called_once_with(self.mock_session, "cookie_token")
        mock_user_repo.get_user_by_id.assert_called_once_with(self.mock_session, "1")

    @patch("usecase.login.SessionRepositoryIf")
    async def test_auth_session_no_token(self, mock_session_repository_class):
        """
        Given: トークンが含まれないリクエスト
        When: auth_sessionメソッドを呼び出す
        Then: 空文字列でセッション検索が呼ばれること
        """

        # Given
        request = self.create_mock_request()

        # モックの設定
        mock_session_repo = AsyncMock()
        mock_session_repo.get_session_by_token.return_value = None
        mock_session_repository_class.return_value = mock_session_repo

        self.use_case.session_repo = mock_session_repo

        # When
        result = await self.use_case.auth_session(self.mock_session, request)

        # Then
        self.assertIsNone(result)
        mock_session_repo.get_session_by_token.assert_called_once_with(self.mock_session, "")

    @patch("usecase.login.SessionRepositoryIf")
    async def test_auth_session_invalid_token(self, mock_session_repository_class):
        """
        Given: 無効なセッショントークンを含むリクエスト
        When: auth_sessionメソッドを呼び出す
        Then: Noneが返されること
        """

        # Given
        request = self.create_mock_request(cookies={"session_token": "invalid_token"})

        # モックの設定
        mock_session_repo = AsyncMock()
        mock_session_repo.get_session_by_token.return_value = None
        mock_session_repository_class.return_value = mock_session_repo

        self.use_case.session_repo = mock_session_repo

        # When
        result = await self.use_case.auth_session(self.mock_session, request)

        # Then
        self.assertIsNone(result)
        mock_session_repo.get_session_by_token.assert_called_once_with(self.mock_session, "invalid_token")

    @patch("usecase.login.SessionRepositoryIf")
    async def test_auth_session_malformed_authorization_header(self, mock_session_repository_class):
        """
        Given: 不正な形式のAuthorizationヘッダーを含むリクエスト
        When: auth_sessionメソッドを呼び出す
        Then: 適切にトークンが抽出されること
        """

        # Given
        request = self.create_mock_request(headers={"Authorization": "Invalid token"})

        # モックの設定
        mock_session_repo = AsyncMock()
        mock_session_repo.get_session_by_token.return_value = None
        mock_session_repository_class.return_value = mock_session_repo

        self.use_case.session_repo = mock_session_repo

        # When
        result = await self.use_case.auth_session(self.mock_session, request)

        # Then
        self.assertIsNone(result)
        # "Bearer "が含まれていないため、そのまま使用される
        mock_session_repo.get_session_by_token.assert_called_once_with(self.mock_session, "Invalid token")


if __name__ == "__main__":
    unittest.main()
