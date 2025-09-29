from database import get_session
from dependencies import get_injector
from fastapi import APIRouter, Depends, HTTPException, Request, status
from schema.message_schema import MessageCreateRequest, MessageResponse
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.channel_access_checker import ChannelAccessCheckerUseCaseIf
from usecase.create_message import (
    ChannelNotFoundError,
    CreateMessageUseCaseError,
    CreateMessageUseCaseIf,
)
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)

router = APIRouter(prefix="/api")


def get_usecase(injector=Depends(get_injector)) -> CreateMessageUseCaseIf:
    return injector.get(CreateMessageUseCaseIf)


def get_channel_access_checker(injector=Depends(get_injector)) -> ChannelAccessCheckerUseCaseIf:
    return injector.get(ChannelAccessCheckerUseCaseIf)


async def check_channel_access_for_message(
    req: MessageCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    access_checker: ChannelAccessCheckerUseCaseIf = Depends(get_channel_access_checker),
) -> None:
    """メッセージ投稿時のチャンネルアクセス権限をチェックする依存関数"""
    await access_checker.execute(request, str(req.channel_id), session)


# チャネルにメッセージを送信するエンドポイント
@router.post("/message", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def post_message_to_channel(
    req: MessageCreateRequest,
    session: AsyncSession = Depends(get_session),
    usecase: CreateMessageUseCaseIf = Depends(get_usecase),
    _: None = Depends(check_channel_access_for_message),  # チャンネルアクセス権限チェック
) -> MessageResponse:
    try:
        response = await usecase.execute(session, req)
        logger.info(f"メッセージが正常に作成されました: message_id={response.id}, channel_id={response.channel_id}")

        return response

    except ChannelNotFoundError as e:
        logger.warning(f"チャンネルが見つかりません: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定されたチャンネルが見つかりません")

    except CreateMessageUseCaseError as e:
        logger.error(f"メッセージ作成ユースケースエラー: {e}")
        if e.original_error:
            logger.error(f"詳細なエラー情報: {e.original_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="メッセージの作成中にエラーが発生しました"
        )

    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サーバー内部エラーが発生しました"
        )
