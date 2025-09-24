from database import get_session
from dependencies import get_injector
from fastapi import APIRouter, Depends, HTTPException, status
from schema.message_schema import MessageCreateRequest, MessageResponse
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.create_message import CreateMessageUseCaseIf
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)

router = APIRouter(prefix="/api")


def get_usecase(injector=Depends(get_injector)) -> CreateMessageUseCaseIf:
    return injector.get(CreateMessageUseCaseIf)


# チャネルにメッセージを送信するエンドポイント
@router.post("/channels/{channel_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def post_message_to_channel(
    req: MessageCreateRequest,
    channel_id: str,
    session: AsyncSession = Depends(get_session),
    usecase: CreateMessageUseCaseIf = Depends(get_usecase),
) -> MessageResponse:
    try:
        response = await usecase.execute(session, req, channel_id)
    except Exception as e:
        logger.error(f"メッセージ作成中にエラー発生: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サーバー内部エラーが発生しました"
        )

    return response
