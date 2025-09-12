from abc import ABC, abstractmethod
from datetime import timedelta

from domains import Session
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from injector import inject, singleton
from repository.session_repository import SessionRepositoryIf
from repository.user_repository import UserRepositoryIf
from sqlalchemy.ext.asyncio import AsyncSession
from utils import create_access_token, verify_password


class LoginUseCaseIf(ABC):
    """ログインユースケースインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @inject
    def __init__(self, user_repo: UserRepositoryIf, session_repo: SessionRepositoryIf) -> None:
        """ログインユースケースの初期化

        Args:
            user_repo (UserRepositoryIf): ユーザーリポジトリ
            session_repo (SessionRepositoryIf): セッションリポジトリ
        """

        self.user_repo: UserRepositoryIf = user_repo
        self.session_repo: SessionRepositoryIf = session_repo

    @abstractmethod
    async def create_session(self, session: AsyncSession, req: Request, form_data: OAuth2PasswordRequestForm) -> dict:
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
    async def auth_session(self, session: AsyncSession, req: Request) -> Session | None:
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

    async def create_session(self, session: AsyncSession, req: Request, form_data: OAuth2PasswordRequestForm) -> dict:
        """セッションを作成する

        Args:
            session (AsyncSession): データベースセッション
            req (Request): HTTPリクエスト
            form_data (OAuth2PasswordRequestForm): フォームデータ

        Returns:
            dict: セッション情報
        """

        # ユーザーの認証
        user = await self.user_repo.get_user_by_username(session, form_data.username)
        if not user or (not await verify_password(str(user.password_hash), form_data.password)):
            return {
                "session": None,
                "user": user,
            }

        # access_tokenの生成
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

        # sessionの保存
        session_db = Session(
            user_id=user.id,
            refresh_token_hash=access_token,
            user_agent=req.headers.get("User-Agent"),
            ip_address=req.client.host if req.client is not None else None,
        )

        session_db: Session | None = await self.session_repo.create_session(session, session_db)

        return {
            "session": session_db,
            "user": user,
        }

    async def auth_session(self, session: AsyncSession, req: Request) -> Session | None:
        """セッションを認証する

        Args:
            session (AsyncSession): データベースセッション
            req (Request): HTTPリクエスト

        Returns:
            Session | None: セッション情報
        """

        # CookieまたはAuthorizationヘッダーからトークンを取得
        token = req.cookies.get("session_token") or req.headers.get("Authorization", "").replace("Bearer ", "")

        return await self.session_repo.get_session_by_token(session, token)
