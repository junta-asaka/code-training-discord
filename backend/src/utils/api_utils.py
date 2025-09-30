from dependencies import get_injector
from fastapi import Depends
from usecase.channel_access_checker import ChannelAccessCheckerUseCaseIf


def get_channel_access_checker(injector=Depends(get_injector)) -> ChannelAccessCheckerUseCaseIf:
    """チャンネルアクセスチェッカーのUseCaseを取得する"""
    return injector.get(ChannelAccessCheckerUseCaseIf)
