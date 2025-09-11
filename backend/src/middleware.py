from database import get_session
from fastapi import Request
from repository.session_repository import SessionRepositoryImpl
from repository.user_repository import UserRepositoryImpl
from usecase.login import LoginUseCaseImpl


async def auth_session(
    req: Request,
):
    """セッション認証を行う

    Args:
        req (Request): HTTPリクエスト

    Returns:
        bool: 認証に成功した場合はTrue、失敗した場合はFalse
    """

    usecase = LoginUseCaseImpl(user_repo=UserRepositoryImpl(), session_repo=SessionRepositoryImpl())
    async for session in get_session():
        if not session or (not await usecase.auth_session(session, req)):
            return False

        return True
