from typing import Any, Awaitable, Callable

from database import get_session
from fastapi import Request
from fastapi.responses import JSONResponse
from repository.session_repository import SessionRepositoryImpl
from repository.user_repository import UserRepositoryImpl
from usecase.login import LoginUseCaseImpl
from utils.utils import is_test_env


async def auth_session(
    req: Request, call_next: Callable[[Request], Awaitable[Any]]
) -> Any:
    """セッション認証を行う

    Args:
        req (Request): HTTPリクエスト
        call_next (_type_): 次のミドルウェアまたはエンドポイントを呼び出す関数

    Returns:
        _type_: HTTPレスポンス
    """

    # テスト環境ではセッション認証をスキップ
    if await is_test_env():
        return await call_next(req)

    # プリフライトリクエスト（OPTIONS）や認証不要のパスをスキップ
    if req.method == "OPTIONS" or req.url.path in [
        "/api/login",
        "/api/user",
        "/auth/refresh",
        "/docs",
        "/openapi.json",
    ]:
        return await call_next(req)

    usecase = LoginUseCaseImpl(
        user_repo=UserRepositoryImpl(), session_repo=SessionRepositoryImpl()
    )

    async for session in get_session():
        result_auth = await usecase.auth_session(session, req)
        if not result_auth:
            return JSONResponse(status_code=401, content={"detail": "認証が必要です"})

        req.state.user = result_auth

        return await call_next(req)
