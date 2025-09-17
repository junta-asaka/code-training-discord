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
        new_hash = hashlib.pbkdf2_hmac("sha256", provided_password.encode(), salt, 100_000)

        return new_hash == expected_hash

    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def is_test_env():
    """テスト環境かどうかを判定する

    Returns:
        bool: テスト環境ならTrue、そうでなければFalse
    """

    if os.getenv("TESTING") == "true":
        return True
    return False
