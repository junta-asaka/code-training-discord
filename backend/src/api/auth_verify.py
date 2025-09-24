from fastapi import APIRouter

router = APIRouter()


@router.get("/auth/verify")
async def verify_session():
    """
    セッション検証用のエンドポイント
    認証ミドルウェアを通過した場合のみアクセス可能
    """

    return {"message": "Session is valid", "authenticated": True}
