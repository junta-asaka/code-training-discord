from sqlalchemy import select
from domains import User
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    # ユーザ作成
    async def create_user(self, session: AsyncSession, user: User) -> User:
        user_db = User(
            name=user.name,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            description=user.description,
        )

        session.add(user_db)
        await session.commit()
        await session.refresh(user_db)

        return user_db

    # ユーザ参照 - 自ユーザのみ
    async def get_user(
        self, session: AsyncSession, username: str, email: str, password_hash: str
    ):
        stmt = select(User).where(
            User.username == username,
            User.email == email,
            User.password_hash == password_hash,
        )
        result = await session.execute(stmt)
        return result.scalars().first()
