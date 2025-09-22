from database import get_session
from dependencies import get_injector
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from schema.login_schema import LoginResponse
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.login import LoginUseCaseIf

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_usecase(injector=Depends(get_injector)) -> LoginUseCaseIf:
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

    result_usecase: dict | None = await usecase.create_session(session, req, form_data)
    user = result_usecase.get("user")
    session_obj = result_usecase.get("session")

    if not user or not session_obj:
        # 失敗時もnextパラメータを含めてエラーレスポンス
        error_detail = {"message": "Unauthorized"}
        if next_param:
            error_detail["next"] = next_param
        raise HTTPException(status_code=401, detail=error_detail)

    # LoginResponseに必要なフィールドのみを抽出
    login_response_data = {
        "name": user.name,
        "username": user.username,
        "access_token": session_obj.refresh_token_hash,  # ここにアクセストークンが保存されている
        "token_type": "bearer",
    }

    # nextパラメータがある場合は追加
    if next_param:
        login_response_data["next"] = next_param

    return LoginResponse.model_validate(login_response_data)
