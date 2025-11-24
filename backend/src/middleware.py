import os
from typing import Any, Awaitable, Callable

from database import get_session
from fastapi import HTTPException, Request, status
from repository.session_repository import SessionRepositoryImpl
from repository.user_repository import UserRepositoryImpl
from usecase.login import LoginUseCaseImpl
from utils.utils import is_test_env

# 認証不要のパスリスト（環境変数から取得、デフォルト値あり）
EXEMPT_PATHS = os.getenv("EXEMPT_PATHS", "/login,/docs,/openapi.json").split(",")

# DBを更新するリクエストのパスリスト（環境変数から取得、デフォルト値あり）
# これらのパスはJWT検証+DBセッション状態確認を行う
DB_MUTATION_PATHS = os.getenv("DB_MUTATION_PATHS", "/register").split(",")


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
    if req.method == "OPTIONS" or req.url.path in EXEMPT_PATHS:
        return await call_next(req)

    usecase = LoginUseCaseImpl(
        user_repo=UserRepositoryImpl(), session_repo=SessionRepositoryImpl()
    )

    async for session in get_session():
        # DBを更新するリクエストの場合、JWT検証+DBセッション状態確認
        if req.url.path in DB_MUTATION_PATHS:
            result_auth = await usecase.auth_session(session, req)
        else:
            # DBを参照するリクエストの場合、JWT検証のみ
            result_auth = await usecase.auth_jwt_only(session, req)

        if not result_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です",
            )

        req.state.user = result_auth

        return await call_next(req)
