import os
import sys

from injector import Binder, Injector

# テストファイルのルートディレクトリからの相対パスでsrcフォルダを指定
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from repository.user_repository import UserRepositoryIf, UserRepositoryImpl
from usecase.create_user import CreateUserUseCaseIf, CreateUserUseCaseImpl


def configure(binder: Binder):
    """DI紐づけ

    Args:
        binder (Binder): _description_
    """

    # CreateUserUseCaseのバインド
    binder.bind(CreateUserUseCaseIf, to=CreateUserUseCaseImpl)

    # UserRepositoryのバインド
    binder.bind(UserRepositoryIf, to=UserRepositoryImpl)


injector = Injector([configure])


def get_injector():
    return injector
