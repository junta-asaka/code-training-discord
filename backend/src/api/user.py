from database import get_session
from dependencies import get_injector
from fastapi import APIRouter, Depends, HTTPException, status
from schema.user_schema import UserCreateRequest, UserResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.create_user import CreateUserUseCaseIf

router = APIRouter()


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
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return response
