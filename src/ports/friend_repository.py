from abc import ABC, abstractmethod

from src.domain.models import Friend


class FriendRepository(ABC):
    @abstractmethod
    def load_friends(self) -> list[Friend]:
        ...
