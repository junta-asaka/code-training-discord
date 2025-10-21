from database import get_session
from dependencies import get_injector
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from injector import Injector
from schema.login_schema import LoginResponse
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.login import LoginTransactionError, LoginUseCaseIf
from utils.logger_utils import get_logger

router = APIRouter(prefix="/api")

# ロガーを取得
logger = get_logger(__name__)


def get_usecase(injector: Injector = Depends(get_injector)) -> LoginUseCaseIf:
    return injector.get(LoginUseCaseIf)


@router.post("/login", response_model=LoginResponse)
async def login(
    req: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
    usecase: LoginUseCaseIf = Depends(get_usecase),
) -> LoginResponse:
    """ログイン処理

    Args:
        req (Request): HTTPリクエスト
        form_data (OAuth2PasswordRequestForm, optional): フォームデータ
        session (_type_, optional): セッション情報
        usecase (LoginUseCaseIf, optional): ログインユースケース

    Raises:
        HTTPException: 認証に失敗した場合

    Returns:
        _type_: ログインレスポンス
    """

    # nextパラメータを取得
    next_param = req.query_params.get("next")

    try:
        result_usecase: dict | None = await usecase.create_session(
            session, req, form_data
        )

    except LoginTransactionError as e:
        logger.error(f"ログイン処理中にエラーが発生: {e}")
        if e.original_error:
            logger.error(f"詳細なエラー情報: {e.original_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログイン中にエラーが発生しました",
        )

    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="サーバー内部エラーが発生しました",
        )

    if result_usecase is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ログインに失敗しました",
        )

    user = result_usecase.get("user")
    session_obj = result_usecase.get("session")

    if not user or not session_obj:
        # 失敗時もnextパラメータを含めてエラーレスポンス
        error_detail = {"message": "Unauthorized"}
        if next_param:
            error_detail["next"] = next_param
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=error_detail
        )

    # LoginResponseに必要なフィールドのみを抽出
    login_response_data = {
        "id": user.id,
        "name": user.name,
        "username": user.username,
        "access_token": session_obj.access_token_hash,  # 適切なフィールド名を使用
        "refresh_token": session_obj.refresh_token_hash,  # リフレッシュトークンも含める
        "token_type": "bearer",
    }

    # nextパラメータがある場合は追加
    if next_param:
        login_response_data["next"] = next_param

    return LoginResponse.model_validate(login_response_data)
