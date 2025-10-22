from datetime import datetime, timedelta, timezone

from database import get_session
from domains import Session
from fastapi import APIRouter, Depends, HTTPException, status
from injector import Injector
from pydantic import BaseModel
from repository.session_repository import SessionRepositoryIf, SessionRepositoryImpl
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from utils.utils import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    verify_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["認証"])


# 依存性注入の設定
def get_session_repository() -> SessionRepositoryIf:
    injector = Injector()
    return injector.get(SessionRepositoryImpl)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒単位


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
    session_repo: SessionRepositoryIf = Depends(get_session_repository),
) -> RefreshTokenResponse:
    """
    リフレッシュトークンを使用して新しいアクセストークンを取得する

    Args:
        request: リフレッシュトークンを含むリクエスト
        session: データベースセッション
        session_repo: セッションリポジトリ

    Returns:
        RefreshTokenResponse: 新しいアクセストークンとリフレッシュトークン

    Raises:
        HTTPException: リフレッシュトークンが無効な場合
    """

    # リフレッシュトークンの検証
    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なリフレッシュトークンです",
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンにユーザー情報が含まれていません",
        )

    # データベースでセッションを確認
    try:
        session_obj = await session_repo.get_session_by_token(
            session, request.refresh_token
        )
        if not session_obj or session_obj.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="セッションが見つからないか、無効化されています",
            )

        # リフレッシュトークンの有効期限確認
        current_time = datetime.now(timezone.utc)
        # SQLAlchemyモデルの属性から実際の値を取得
        expires_at = getattr(session_obj, "refresh_token_expires_at")
        if expires_at and expires_at <= current_time:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="リフレッシュトークンの有効期限が切れています",
            )

        # 新しいアクセストークンを生成
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )

        # SQLAlchemyオブジェクトの属性を更新（値を直接更新）

        # セッションの更新
        update_stmt = (
            update(Session)
            .where(Session.id == session_obj.id)
            .values(
                access_token_hash=new_access_token,
                access_token_expires_at=current_time + access_token_expires,
            )
        )

        await session.execute(update_stmt)
        await session.commit()

        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=request.refresh_token,  # 既存のリフレッシュトークンをそのまま返す
            expires_in=int(access_token_expires.total_seconds()),
        )

    except HTTPException:
        raise
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="トークンリフレッシュ中にエラーが発生しました",
        )
