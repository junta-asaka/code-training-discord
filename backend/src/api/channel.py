from database import get_session
from dependencies import get_injector
from fastapi import APIRouter, Depends, HTTPException, Request, status
from schema.channel_schema import ChannelGetResponse
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.channel_access_checker import ChannelAccessCheckerUseCaseIf
from usecase.get_channel_messages import (
    ChannelNotFoundError,
    GetChannelMessagesUseCaseError,
    GetChannelMessagesUseCaseIf,
)
from utils.api_utils import get_channel_access_checker
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)

router = APIRouter(prefix="/api")


def get_usecase(injector=Depends(get_injector)) -> GetChannelMessagesUseCaseIf:
    return injector.get(GetChannelMessagesUseCaseIf)


async def check_channel_access(
    channel_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    access_checker: ChannelAccessCheckerUseCaseIf = Depends(get_channel_access_checker),
) -> None:
    """チャンネルアクセス権限をチェックする共通関数"""
    await access_checker.execute(request, channel_id, session)


@router.get("/channels/{channel_id}", response_model=ChannelGetResponse, status_code=status.HTTP_200_OK)
async def get_channel(
    channel_id: str,
    session: AsyncSession = Depends(get_session),
    usecase: GetChannelMessagesUseCaseIf = Depends(get_usecase),
    _: None = Depends(check_channel_access),  # チャンネルアクセス権限チェック
) -> ChannelGetResponse:
    try:
        response = await usecase.execute(session, channel_id)
        logger.info(
            f"チャンネル情報が正常に取得されました: channel_id={channel_id}, message_count={len(response.messages)}"
        )

        return response

    except ChannelNotFoundError as e:
        logger.warning(f"チャンネルが見つかりません: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定されたチャンネルが見つかりません")

    except GetChannelMessagesUseCaseError as e:
        logger.error(f"チャンネル取得ユースケースエラー: {e}")
        if e.original_error:
            logger.error(f"詳細なエラー情報: {e.original_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="チャンネル情報の取得中にエラーが発生しました"
        )

    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サーバー内部エラーが発生しました"
        )
