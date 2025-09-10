from injector import Binder, Injector

from usecase.create_user import CreateUserUseCaseIf, CreateUserUseCaseImpl


def configure(binder: Binder):
    """DI紐づけ

    Args:
        binder (Binder): _description_
    """

    # CreateUserUseCaseのバインド
    binder.bind(CreateUserUseCaseIf, to=CreateUserUseCaseImpl)


injector = Injector([configure])


def get_injector():
    return injector
