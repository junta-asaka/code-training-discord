class BaseMessageUseCaseError(Exception):
    """ユースケース基底例外クラス"""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error
