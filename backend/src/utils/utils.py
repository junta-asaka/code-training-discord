import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

import jwt
from dotenv import load_dotenv

# .envファイルの内容を読み込見込む
load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]

# トークン有効期限の設定（環境変数から取得、デフォルト値あり）
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


async def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    # パスワードをソルト付きでハッシュ化し、ソルトとハッシュを保存可能な文字列として返す

    if salt is None:
        salt = os.urandom(16)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    hash_b64 = base64.b64encode(hash_bytes).decode("utf-8")

    return f"{salt_b64}${hash_b64}"


async def verify_password(stored_password: str, provided_password: str) -> bool:
    try:
        salt_b64, hash_b64 = stored_password.split("$")
        salt = base64.b64decode(salt_b64)
        expected_hash = base64.b64decode(hash_b64)
        new_hash = hashlib.pbkdf2_hmac(
            "sha256", provided_password.encode(), salt, 100_000
        )

        return new_hash == expected_hash

    except Exception:
        return False


def hash_token(token: str) -> str:
    """トークンをSHA-256でハッシュ化する

    Args:
        token (str): ハッシュ化するトークン

    Returns:
        str: ハッシュ化されたトークン（16進数文字列）
    """

    return hashlib.sha256(token.encode()).hexdigest()


def create_token(
    data: dict,
    token_type: str = "access",
    expires_delta: Union[timedelta, None] = None,
) -> str:
    """JWTトークンを生成する

    Args:
        data (dict): JWTペイロードに含めるデータ
        token_type (str): トークンタイプ（"access" または "refresh"）。デフォルトは "access"
        expires_delta (Union[timedelta, None], optional): 有効期限の設定

    Returns:
        str: JWTトークン
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        if token_type == "access":
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        else:  # refresh
            expire = datetime.now(timezone.utc) + timedelta(
                days=REFRESH_TOKEN_EXPIRE_DAYS
            )
    to_encode.update({"exp": expire, "type": token_type})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """JWTトークンを検証する

    Args:
        token (str): JWTトークン
        token_type (str): トークンタイプ（"access" または "refresh"）。デフォルトは "access"

    Returns:
        Optional[dict]: トークンが有効な場合はペイロード、無効な場合はNone
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # トークンタイプを確認
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def is_test_env() -> bool:
    """テスト環境かどうかを判定する

    Returns:
        bool: テスト環境ならTrue、そうでなければFalse
    """

    if os.getenv("TESTING") == "true":
        return True
    return False
