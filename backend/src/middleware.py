from database import get_session
from fastapi import Request
from fastapi.responses import JSONResponse
from repository.session_repository import SessionRepositoryImpl
from repository.user_repository import UserRepositoryImpl
from usecase.login import LoginUseCaseImpl


async def auth_session(req: Request, call_next):
    """セッション認証を行う

    Args:
        req (Request): HTTPリクエスト
        call_next (_type_): 次のミドルウェアまたはエンドポイントを呼び出す関数

    Returns:
        _type_: HTTPレスポンス
    """

    if req.url.path in ["/login", "/register", "/docs", "/openapi.json"]:
        return await call_next(req)

    usecase = LoginUseCaseImpl(user_repo=UserRepositoryImpl(), session_repo=SessionRepositoryImpl())

    async for session in get_session():
        if not session or (not await usecase.auth_session(session, req)):
            return JSONResponse(status_code=401, content="Unauthorized")

        return await call_next(req)
