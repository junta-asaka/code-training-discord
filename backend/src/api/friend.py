from uuid import UUID

from database import get_session
from dependencies import get_injector
from fastapi import APIRouter, Depends, HTTPException, status
from schema.friend_schema import (
    FriendCreateRequest,
    FriendCreateResponse,
    FriendGetResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.friend import FriendUseCaseIf

router = APIRouter(prefix="/api")


def get_usecase(injector=Depends(get_injector)) -> FriendUseCaseIf:
    return injector.get(FriendUseCaseIf)


@router.post("/friend", response_model=FriendCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_friend(
    req: FriendCreateRequest,
    session: AsyncSession = Depends(get_session),
    usecase: FriendUseCaseIf = Depends(get_usecase),
) -> FriendCreateResponse:
    """フレンド作成処理

    Args:
        req (FriendCreateRequest): フレンド作成リクエスト
        session (_type_, optional): データベースセッション
        usecase (FriendUseCaseIf, optional): フレンドユースケース

    Raises:
        HTTPException: フレンド作成に失敗した場合

    Returns:
        FriendCreateResponse: フレンド作成レスポンス
    """

    try:
        friend = await usecase.create_friend(session, req)
    except Exception:
        # ログ出力などの処理を追加
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サーバー内部エラーが発生しました"
        )

    if not friend:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create friend")

    return FriendCreateResponse.model_validate(friend)


@router.get("/friends", response_model=list[FriendGetResponse], status_code=status.HTTP_200_OK)
async def get_friends(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    usecase: FriendUseCaseIf = Depends(get_usecase),
) -> list[FriendGetResponse]:
    """フレンド一覧取得処理

    Args:
        user_id (str): ユーザーID
        session (_type_, optional): データベースセッション
        usecase (FriendUseCaseIf, optional): フレンドユースケース

    Returns:
        list[FriendGetResponse]: フレンド一覧レスポンス
    """

    try:
        UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なユーザーIDです")

    users = await usecase.get_friend_all(session, user_id)
    if users is None:
        return []

    return [FriendGetResponse.model_validate(user) for user in users]
