from abc import ABC, abstractmethod

from src.domain.models import Message


class MessageSender(ABC):
    @abstractmethod
    def send(self, message: Message) -> None:
        ...
