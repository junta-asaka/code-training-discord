import os
import base64
import hashlib
from typing import Optional


async def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    # パスワードをソルト付きでハッシュ化し、ソルトとハッシュを保存可能な文字列として返す

    if salt is None:
        salt = os.urandom(16)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    hash_b64 = base64.b64encode(hash_bytes).decode("utf-8")

    return f"{salt_b64}${hash_b64}"
