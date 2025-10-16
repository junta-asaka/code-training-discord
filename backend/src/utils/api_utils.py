from dependencies import get_injector
from fastapi import Depends
from injector import Injector
from usecase.channel_access_checker import ChannelAccessCheckerUseCaseIf


def get_channel_access_checker(
    injector: Injector = Depends(get_injector),
) -> ChannelAccessCheckerUseCaseIf:
    """チャンネルアクセスチェッカーのUseCaseを取得する"""
    return injector.get(ChannelAccessCheckerUseCaseIf)
