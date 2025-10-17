from uuid import UUID

from fastapi import HTTPException, status


def validate_user_id(user_id: str) -> str:
    """ユーザーIDのバリデーション処理

    Args:
        user_id (str): バリデーション対象のユーザーID

    Raises:
        HTTPException: 無効なユーザーIDの場合

    Returns:
        str: バリデーション済みのユーザーID
    """

    try:
        UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="無効なユーザーIDです"
        )

    return user_id


def validate_channel_id(channel_id: str) -> str:
    """チャンネルIDのバリデーション処理

    Args:
        channel_id (str): バリデーション対象のチャンネルID

    Raises:
        HTTPException: 無効なチャンネルIDの場合

    Returns:
        str: バリデーション済みのチャンネルID
    """

    try:
        UUID(channel_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="無効なチャンネルIDです"
        )

    return channel_id
