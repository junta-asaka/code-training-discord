from abc import ABC

from injector import inject, singleton
from repository.channel_repository import ChannelRepositoryIf


class ChannelUseCaseIf(ABC):
    @inject
    def __init__(self, channel_repo: ChannelRepositoryIf):
        self.channel_repo = channel_repo


@singleton
class ChannelUseCaseImpl(ChannelUseCaseIf):
    pass
