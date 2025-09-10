from abc import ABC, abstractmethod
from datetime import timedelta

from domains import Session
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from injector import inject, singleton
from repository.session_repository import SessionRepositoryIf
from repository.user_repository import UserRepositoryImpl
from sqlalchemy.ext.asyncio import AsyncSession
from utils import create_access_token, verify_password


class LoginUseCaseIf(ABC):
    @inject
    def __init__(self, user_repo: UserRepositoryImpl, session_repo: SessionRepositoryIf) -> None:
        self.user_repo: UserRepositoryImpl = user_repo
        self.session_repo: SessionRepositoryIf = session_repo

    @abstractmethod
    async def create_session(
        self, session: AsyncSession, req: Request, form_data: OAuth2PasswordRequestForm
    ) -> Session | None:
        pass

    @abstractmethod
    async def auth_session(self, session: AsyncSession, req: Request) -> Session | None:
        pass


@singleton
class LoginUseCaseImpl(LoginUseCaseIf):
    async def create_session(
        self, session: AsyncSession, req: Request, form_data: OAuth2PasswordRequestForm
    ) -> Session | None:
        # ユーザーの認証
        user = await self.user_repo.get_user_by_username(session, form_data.username)
        if not user or verify_password(str(user.password_hash), form_data.password):
            return None

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

        return await self.session_repo.create_session(session, session_db)

    async def auth_session(self, session: AsyncSession, req: Request) -> Session | None:
        token = req.cookies.get("session_token") or req.headers.get("Authorization", "").replace("Bearer ", "")

        return await self.session_repo.get_session_by_token(session, token)
