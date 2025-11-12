from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from domains import Session, User
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from injector import inject, singleton
from repository.session_repository import SessionRepositoryError, SessionRepositoryIf
from repository.user_repository import UserRepositoryError, UserRepositoryIf
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.base_exception import BaseMessageUseCaseError
from utils.logger_utils import get_logger
from utils.utils import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_password,
)

# ロガーを取得
logger = get_logger(__name__)


class LoginUseCaseError(BaseMessageUseCaseError):
    """ログインユースケース例外クラス"""

    pass


class LoginTransactionError(LoginUseCaseError):
    """ログインのトランザクションエラー"""

    pass


class LoginUseCaseIf(ABC):
    """ログインユースケースインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @inject
    def __init__(
        self, user_repo: UserRepositoryIf, session_repo: SessionRepositoryIf
    ) -> None:
        """ログインユースケースの初期化

        Args:
            user_repo (UserRepositoryIf): ユーザーリポジトリ
            session_repo (SessionRepositoryIf): セッションリポジトリ
        """

        self.user_repo: UserRepositoryIf = user_repo
        self.session_repo: SessionRepositoryIf = session_repo

    @abstractmethod
    async def create_session(
        self, session: AsyncSession, req: Request, form_data: OAuth2PasswordRequestForm
    ) -> dict:
        """セッションを作成する

        Args:
            session (AsyncSession): データベースセッション
            req (Request): HTTPリクエスト
            form_data (OAuth2PasswordRequestForm): フォームデータ

        Returns:
            dict: セッション情報
        """

        pass

    @abstractmethod
    async def auth_session(self, session: AsyncSession, req: Request) -> User | None:
        """セッションを認証する

        Args:
            session (AsyncSession): データベースセッション
            req (Request): HTTPリクエスト

        Returns:
            Session | None: セッション情報
        """

        pass


@singleton
class LoginUseCaseImpl(LoginUseCaseIf):
    """ログインユースケース実装

    Args:
        LoginUseCaseIf (_type_): ログインユースケースインターフェース
    """

    async def create_session(
        self, session: AsyncSession, req: Request, form_data: OAuth2PasswordRequestForm
    ) -> dict:
        """セッションを作成する

        Args:
            session (AsyncSession): データベースセッション
            req (Request): HTTPリクエスト
            form_data (OAuth2PasswordRequestForm): フォームデータ

        Returns:
            dict: セッション情報
        """

        try:
            # ユーザーの認証
            user = await self.user_repo.get_user_by_username(
                session, form_data.username
            )
            if not user or (
                not await verify_password(str(user.password_hash), form_data.password)
            ):
                return {
                    "session": None,
                    "user": user,
                }

            # アクセストークンとリフレッシュトークンの生成
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

            access_token = create_access_token(
                data={"sub": user.username}, expires_delta=access_token_expires
            )
            refresh_token = create_refresh_token(
                data={"sub": user.username}, expires_delta=refresh_token_expires
            )

            # 有効期限の計算
            access_expires_at = datetime.now(timezone.utc) + access_token_expires
            refresh_expires_at = datetime.now(timezone.utc) + refresh_token_expires

            # sessionの保存
            session_db = Session(
                user_id=user.id,
                access_token=access_token,
                refresh_token=refresh_token,
                access_token_expires_at=access_expires_at,
                refresh_token_expires_at=refresh_expires_at,
                user_agent=req.headers.get("User-Agent"),
                ip_address=req.client.host if req.client is not None else None,
            )

            created_session: Session | None = await self.session_repo.create_session(
                session, session_db
            )

            return {
                "session": created_session,
                "user": user,
            }

        except UserRepositoryError as e:
            raise LoginTransactionError("ユーザー取得中にエラーが発生しました", e)

        except SessionRepositoryError as e:
            raise LoginTransactionError("セッション作成中にエラーが発生しました", e)

        except Exception as e:
            raise LoginTransactionError("予期しないエラーが発生しました", e)

    async def auth_session(self, session: AsyncSession, req: Request) -> User | None:
        """セッションを認証する（JWT検証を活用してDB負荷を軽減）

        Args:
            session (AsyncSession): データベースセッション
            req (Request): HTTPリクエスト

        Returns:
            User | None: ユーザー情報
        """

        try:
            # CookieまたはAuthorizationヘッダーからトークンを取得
            token = req.cookies.get("session_token") or req.headers.get(
                "Authorization", ""
            ).replace("Bearer ", "")

            if not token:
                return None

            # まずJWTトークンの検証（DB検索なし）
            payload = verify_access_token(token)
            if not payload:
                return None

            username = payload.get("sub")
            if not username:
                return None

            # JWTが有効な場合のみ、ユーザー情報を取得
            return await self.user_repo.get_user_by_username(session, username)

        except SessionRepositoryError as e:
            raise LoginTransactionError("セッション取得中にエラーが発生しました", e)

        except Exception as e:
            raise LoginTransactionError("予期しないエラーが発生しました", e)
