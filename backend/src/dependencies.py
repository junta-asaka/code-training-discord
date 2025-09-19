from injector import Binder, Injector
from repository.friend_repository import FriendRepositoryIf, FriendRepositoryImpl
from repository.guild_member_repository import GuildMemberRepositoryIf, GuildMemberRepositoryImpl
from repository.guild_repository import GuildRepositoryIf, GuildRepositoryImpl
from repository.session_repository import SessionRepositoryIf, SessionRepositoryImpl
from repository.user_repository import UserRepositoryIf, UserRepositoryImpl
from usecase.create_user import CreateUserUseCaseIf, CreateUserUseCaseImpl
from usecase.friend import FriendUseCaseIf, FriendUseCaseImpl
from usecase.login import LoginUseCaseIf, LoginUseCaseImpl


def configure(binder: Binder):
    """DI紐づけ

    Args:
        binder (Binder): _description_
    """

    # CreateUserUseCaseのバインド
    binder.bind(CreateUserUseCaseIf, to=CreateUserUseCaseImpl)
    # LoginUseCaseのバインド
    binder.bind(LoginUseCaseIf, to=LoginUseCaseImpl)
    # FriendUseCaseのバインド
    binder.bind(FriendUseCaseIf, to=FriendUseCaseImpl)

    # UserRepositoryのバインド
    binder.bind(UserRepositoryIf, to=UserRepositoryImpl)
    # SessionRepositoryのバインド
    binder.bind(SessionRepositoryIf, to=SessionRepositoryImpl)
    # FriendRepositoryのバインド
    binder.bind(FriendRepositoryIf, to=FriendRepositoryImpl)
    # GuildRepositoryのバインド
    binder.bind(GuildRepositoryIf, to=GuildRepositoryImpl)
    # GuildMemberRepositoryのバインド
    binder.bind(GuildMemberRepositoryIf, to=GuildMemberRepositoryImpl)


injector = Injector([configure])


def get_injector():
    return injector
