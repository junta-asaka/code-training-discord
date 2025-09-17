from database import get_session
from dependencies import get_injector
from fastapi import APIRouter, Depends, HTTPException, status
from schema.friend_schema import FriendCreateRequest, FriendCreateResponse, FriendGetResponse
from usecase.friend import FriendUseCaseIf

router = APIRouter(prefix="/api")


def get_usecase(injector=Depends(get_injector)) -> FriendUseCaseIf:
    return injector.get(FriendUseCaseIf)


@router.post("/friend", response_model=FriendCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_friend(
    req: FriendCreateRequest,
    session=Depends(get_session),
    usecase: FriendUseCaseIf = Depends(get_usecase),
):
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

    friend = await usecase.create_friend(session, req)
    if not friend:
        raise HTTPException(status_code=400, detail="Failed to create friend")

    return FriendCreateResponse(
        id=str(friend.id),
        user_id=str(friend.user_id),
        related_user_id=str(friend.related_user_id),
        type=str(friend.type),
        created_at=friend.created_at.isoformat(),
    )


@router.get("/friends", response_model=list[FriendGetResponse], status_code=status.HTTP_200_OK)
async def get_friends(
    user_id: str,
    session=Depends(get_session),
    usecase: FriendUseCaseIf = Depends(get_usecase),
):
    """フレンド一覧取得処理

    Args:
        user_id (str): ユーザーID
        session (_type_, optional): データベースセッション
        usecase (FriendUseCaseIf, optional): フレンドユースケース

    Returns:
        list[FriendGetResponse]: フレンド一覧レスポンス
    """

    users = await usecase.get_friend_all(session, user_id)
    if users is None:
        return []

    return [
        FriendGetResponse(
            name=str(user.name),
            username=str(user.username),
            description=str(user.description),
            created_at=user.created_at.isoformat(),
        )
        for user in users
    ]
