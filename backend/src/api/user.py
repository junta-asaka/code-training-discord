from database import get_session
from dependencies import get_injector
from fastapi import APIRouter, Depends, HTTPException, status
from schema.user_schema import UserCreateRequest, UserResponse
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.create_user import CreateUserTransactionError, CreateUserUseCaseIf
from utils.logger_utils import get_logger

router = APIRouter(prefix="/api")

# ロガーを取得
logger = get_logger(__name__)


def get_usecase(injector=Depends(get_injector)) -> CreateUserUseCaseIf:
    return injector.get(CreateUserUseCaseIf)


@router.post("/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    req: UserCreateRequest,
    session: AsyncSession = Depends(get_session),
    usecase: CreateUserUseCaseIf = Depends(get_usecase),
) -> UserResponse:
    try:
        response = await usecase.execute(session, req)

        return response

    except CreateUserTransactionError as e:
        logger.error(f"ユーザー作成ユースケースエラー: {e}")
        if e.original_error:
            logger.error(f"詳細なエラー情報: {e.original_error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ユーザー作成中にエラーが発生しました")

    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サーバー内部エラーが発生しました"
        )
