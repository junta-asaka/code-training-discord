from injector import Binder, Injector
from repository.session_repository import SessionRepositoryIf, SessionRepositoryImpl
from repository.user_repository import UserRepositoryIf, UserRepositoryImpl
from usecase.create_user import CreateUserUseCaseIf, CreateUserUseCaseImpl
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

    # UserRepositoryのバインド
    binder.bind(UserRepositoryIf, to=UserRepositoryImpl)
    # SessionRepositoryのバインド
    binder.bind(SessionRepositoryIf, to=SessionRepositoryImpl)


injector = Injector([configure])


def get_injector():
    return injector
