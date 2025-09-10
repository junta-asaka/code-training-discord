from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_injector
from database import get_session
from usecase.create_user import CreateUserUseCaseIf
from schema.user_schema import UserCreateRequest, UserResponse

router = APIRouter()


def get_usecase(injector=Depends(get_injector)) -> CreateUserUseCaseIf:
    return injector.get(CreateUserUseCaseIf)


@router.post("/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    req: UserCreateRequest,
    session: AsyncSession = Depends(get_session),
    usecase: CreateUserUseCaseIf = Depends(get_usecase),
):
    try:
        user_db = await usecase.execute(session, req)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return UserResponse(
        id=str(user_db.id),
        name=str(user_db.name),
        username=str(user_db.username),
        email=str(user_db.email),
        description=str(user_db.description),
        created_at=user_db.created_at.isoformat(),
        updated_at=user_db.updated_at.isoformat(),
    )
