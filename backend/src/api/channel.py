from database import get_session
from dependencies import get_injector
from fastapi import APIRouter, Depends, HTTPException, status
from schema.channel_schema import ChannelGetResponse
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.get_channel_messages import GetChannelMessagesUseCaseIf
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)

router = APIRouter(prefix="/api")


def get_usecase(injector=Depends(get_injector)) -> GetChannelMessagesUseCaseIf:
    return injector.get(GetChannelMessagesUseCaseIf)


@router.get("/channel", response_model=ChannelGetResponse, status_code=status.HTTP_201_CREATED)
async def get_channels(
    channel_id: str,
    session: AsyncSession = Depends(get_session),
    usecase: GetChannelMessagesUseCaseIf = Depends(get_usecase),
) -> ChannelGetResponse:
    try:
        response = await usecase.execute(session, channel_id)
    except Exception as e:
        logger.error(f"チャネル取得中にエラー発生: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サーバー内部エラーが発生しました"
        )

    return response
