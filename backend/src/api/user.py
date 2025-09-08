from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
from usecase.create_user import CreateUserUseCaseImpl
from repository.user_repository import UserRepository
from schema.user_schema import UserCreateRequest, UserResponse
from typing import AsyncGenerator

router = APIRouter()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    req: UserCreateRequest, session: AsyncSession = Depends(get_session)
):
    usecase = CreateUserUseCaseImpl(UserRepository())
    try:
        user_db = await usecase.execute(session, req)
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
