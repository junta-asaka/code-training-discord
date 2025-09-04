from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

DB_URL = "postgresql+psycopg2://jun12:jun12@localhost:5432/jun12"

engine = create_engine(DB_URL, echo=True, pool_pre_ping=True, future=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__: str = "users"
    id: Column[int] = Column(Integer, primary_key=True, index=True)
    name: Column[str] = Column(String, index=True)
    email: Column[str] = Column(String, unique=True, index=True)
    hashed_password: Column[str] = Column(String)
    created_at: Column[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )


def crate_tables() -> None:
    Base.metadata.create_all(bind=engine)


def create_user(session, name, email, hashed_password) -> User:
    new_user = User(name=name, email=email, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user


def get_user(session, user_id) -> User | None:
    return session.query(User).filter(User.id == user_id).first()


def update_user(
    session, user_id, name=None, email=None, hashed_password=None
) -> User | None:
    user: User = session.query(User).filter(User.id == user_id).first()
    if user:
        if name:
            user.name = name
        if email:
            user.email = email
        if hashed_password:
            user.hashed_password = hashed_password
        session.commit()
        session.refresh(user)

    return user


def delete_user(session, user_id) -> User | None:
    user: User = session.query(User).filter(User.id == user_id).first()
    if user:
        session.delete(user)
        session.commit()

    return user


if __name__ == "__main__":
    crate_tables()
    session = Session()

    # Example usage
    user = create_user(
        session=session,
        name="John Doe",
        email="aaa@com",
        hashed_password="hashedpassword123",
    )
    print(f"Created User: {user.id}, {user.name}, {user.email}")

    user = get_user(session=session, user_id=user.id)
    print(f"Retrieved User: {user.id}, {user.name}, {user.email}")

    user = update_user(session=session, user_id=user.id, name="Jane Doe")
    print(f"Updated User: {user.id}, {user.name}, {user.email}")

    user = delete_user(session=session, user_id=user.id)
    print(f"Deleted User: {user.id}, {user.name}, {user.email}")
    user = get_user(session=session, user_id=user.id)
    print(f"Post-Deletion Retrieval (should be None): {user}")
