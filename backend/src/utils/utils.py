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


def create_access_token(
    data: dict, expires_delta: Union[timedelta, None] = None
) -> str:
    """アクセストークンを生成する（短期間有効）

    Args:
        data (dict): JWTペイロードに含めるデータ
        expires_delta (Union[timedelta, None], optional): 有効期限の設定

    Returns:
        str: JWTアクセストークン
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: dict, expires_delta: Union[timedelta, None] = None
) -> str:
    """リフレッシュトークンを生成する（長期間有効）

    Args:
        data (dict): JWTペイロードに含めるデータ
        expires_delta (Union[timedelta, None], optional): 有効期限の設定

    Returns:
        str: JWTリフレッシュトークン
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Optional[dict]:
    """JWTアクセストークンを検証する

    Args:
        token (str): JWTトークン

    Returns:
        Optional[dict]: トークンが有効な場合はペイロード、無効な場合はNone
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # アクセストークンであることを確認
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(token: str) -> Optional[dict]:
    """JWTリフレッシュトークンを検証する

    Args:
        token (str): JWTリフレッシュトークン

    Returns:
        Optional[dict]: トークンが有効な場合はペイロード、無効な場合はNone
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # リフレッシュトークンであることを確認
        if payload.get("type") != "refresh":
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
