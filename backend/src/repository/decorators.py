from functools import wraps
from typing import Type

from repository.base_exception import BaseRepositoryError
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from utils.logger_utils import get_logger

logger = get_logger(__name__)


def handle_repository_errors(error_class: Type[Exception], operation_name: str):
    """リポジトリ操作のエラーハンドリングデコレータ

    Args:
        error_class (Type[Exception]): エラークラス
        operation_name (str): 操作名
    """

    def decorator(func):
        """リポジトリ操作のエラーハンドリングデコレータ"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)

            except IntegrityError as e:
                await args[1].rollback()  # args[1] = session
                error_msg = f"データベース制約違反により [{operation_name}] に失敗"
                logger.error(f"{error_msg}: {e}")
                raise error_class(error_msg, e)

            except OperationalError as e:
                if "rollback" in dir(args[1]):
                    await args[1].rollback()
                error_msg = f"データベース接続エラーにより [{operation_name}] に失敗"
                logger.error(f"{error_msg}: {e}")
                raise error_class(error_msg, e)

            except SQLAlchemyError as e:
                if "rollback" in dir(args[1]):
                    await args[1].rollback()
                error_msg = f"SQLAlchemyエラーにより [{operation_name}] に失敗"
                logger.error(f"{error_msg}: {e}")
                raise error_class(error_msg, e)

            except BaseRepositoryError as e:
                if "rollback" in dir(args[1]):
                    await args[1].rollback()
                error_msg = f"その他リポジトリエラーにより [{operation_name}] に失敗"
                logger.error(f"{error_msg}: {e}")
                # repositoryから定義したカスタムエラーが来る可能性があるため、そのまま再スロー
                raise

            except Exception as e:
                if "rollback" in dir(args[1]):
                    await args[1].rollback()
                error_msg = f"予期しないエラーにより [{operation_name}] に失敗"
                logger.error(f"{error_msg}: {e}")
                raise error_class(error_msg, e)

        return wrapper

    return decorator
