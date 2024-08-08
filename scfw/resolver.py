from abc import (ABCMeta, abstractmethod)

from target import InstallTarget


class InstallTargetsResolver(metaclass=ABCMeta):
    @abstractmethod
    def resolve_targets(self, install_command: list[str]) -> list[InstallTarget]:
        pass