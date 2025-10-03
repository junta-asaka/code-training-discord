from abc import ABC, abstractmethod

from domains import Guild, GuildMember, User
from injector import inject, singleton
from repository.guild_member_repository import GuildMemberRepositoryError, GuildMemberRepositoryIf
from repository.guild_repository import GuildRepositoryError, GuildRepositoryIf
from repository.user_repository import UserRepositoryError, UserRepositoryIf
from schema.user_schema import UserCreateRequest, UserResponse
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.base_exception import BaseMessageUseCaseError
from utils.logger_utils import get_logger
from utils.utils import hash_password

# ロガーを取得
logger = get_logger(__name__)


class CreateUserUseCaseError(BaseMessageUseCaseError):
    """ユーザー作成ユースケース例外クラス"""

    pass


class CreateUserTransactionError(CreateUserUseCaseError):
    """ユーザー作成のトランザクションエラー"""

    pass


class CreateUserUseCaseIf(ABC):
    """ユーザー作成ユースケースインターフェース

    Args:
        ABC (_type_): 抽象クラス
    """

    @inject
    def __init__(
        self, user_repo: UserRepositoryIf, guild_repo: GuildRepositoryIf, guild_member_repo: GuildMemberRepositoryIf
    ) -> None:
        """ユーザー作成ユースケース初期化

        Args:
            user_repo (UserRepositoryIf): ユーザーリポジトリ
            guild_repo (GuildRepositoryIf): ギルドリポジトリ
            guild_member_repo (GuildMemberRepositoryIf): ギルドメンバーリポジトリ
        """

        self.user_repo: UserRepositoryIf = user_repo
        self.guild_repo: GuildRepositoryIf = guild_repo
        self.guild_member_repo: GuildMemberRepositoryIf = guild_member_repo

    @abstractmethod
    async def execute(self, session: AsyncSession, req: UserCreateRequest) -> UserResponse:
        """ユーザー作成ユースケース実行

        Args:
            session (AsyncSession): データベースセッション
            req (UserCreateRequest): ユーザー作成リクエスト

        Returns:
            UserResponse: 作成されたユーザー情報
        """

        pass


@singleton
class CreateUserUseCaseImpl(CreateUserUseCaseIf):
    """ユーザー作成ユースケース実装

    Args:
        CreateUserUseCaseIf (_type_): ユーザー作成ユースケースインターフェース
    """

    async def execute(self, session: AsyncSession, req: UserCreateRequest) -> UserResponse:
        """ユーザー作成ユースケース実行

        Args:
            session (AsyncSession): データベースセッション
            req (UserCreateRequest): ユーザー作成リクエスト

        Returns:
            UserResponse: 作成されたユーザー情報
        """

        try:
            password_hash = await hash_password(req.password)
            user = User(
                name=req.name,
                username=req.username,
                email=req.email,
                password_hash=password_hash,
                description=req.description,
            )
            user_db = await self.user_repo.create_user(session, user)

            guild = Guild(
                owner_user_id=user_db.id,
            )
            guild_db = await self.guild_repo.create_guild(session, guild)

            guild_member = GuildMember(
                user_id=user_db.id,
                guild_id=guild_db.id,
            )
            _ = await self.guild_member_repo.create_guild_member(session, guild_member)

            user_response_data = {
                "id": user_db.id,
                "name": user_db.name,
                "username": user_db.username,
                "email": user_db.email,
                "description": user_db.description,
                "created_at": user_db.created_at.isoformat(),
                "updated_at": user_db.updated_at.isoformat(),
                "guild_id": guild_db.id,
            }

            # すべての操作が成功した場合に commit
            await session.commit()

            return UserResponse.model_validate(user_response_data)

        except UserRepositoryError as e:
            await session.rollback()
            raise CreateUserTransactionError("ユーザー作成中にエラーが発生しました", e)

        except GuildRepositoryError as e:
            await session.rollback()
            raise CreateUserTransactionError("ギルド作成中にエラーが発生しました", e)

        except GuildMemberRepositoryError as e:
            await session.rollback()
            raise CreateUserTransactionError("ギルドメンバー作成中にエラーが発生しました", e)

        except Exception as e:
            await session.rollback()
            raise CreateUserTransactionError("予期しないエラーが発生しました", e)
