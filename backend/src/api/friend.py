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
from usecase.friend import FriendTransactionError, FriendUseCaseIf
from utils.logger_utils import get_logger

router = APIRouter(prefix="/api")

# ロガーを取得
logger = get_logger(__name__)


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

    except FriendTransactionError as e:
        logger.error(f"フレンド作成ユースケースエラー: {e}")
        if e.original_error:
            logger.error(f"詳細なエラー情報: {e.original_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="フレンド作成中にエラーが発生しました"
        )

    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
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

    try:
        response = await usecase.get_friend_all(session, user_id)

        return response

    except FriendTransactionError as e:
        logger.error(f"フレンド取得ユースケースエラー: {e}")
        if e.original_error:
            logger.error(f"詳細なエラー情報: {e.original_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="フレンド取得中にエラーが発生しました"
        )

    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サーバー内部エラーが発生しました"
        )
