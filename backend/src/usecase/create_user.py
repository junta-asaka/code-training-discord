from abc import ABC, abstractmethod
from utils import hash_password
from repository.user_repository import UserRepository
from domains import User
from schema.user_schema import UserCreateRequest
from injector import singleton
from sqlalchemy.ext.asyncio import AsyncSession


class CreateUserUseCaseIf(ABC):
    @abstractmethod
    async def execute(self, session: AsyncSession, req: UserCreateRequest) -> User:
        pass


class CreateUserUseCaseImpl(CreateUserUseCaseIf):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    @singleton
    async def execute(self, session: AsyncSession, req: UserCreateRequest) -> User:
        password_hash = await hash_password(req.password)
        user = User(
            id=None,
            name=req.name,
            username=req.username,
            email=req.email,
            password_hash=password_hash,
            description=req.description,
        )

        return await self.user_repository.create_user(session, user)
