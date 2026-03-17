from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Friend:
    last_name: str
    first_name: str
    date_of_birth: date
    email: str


@dataclass(frozen=True)
class Message:
    to: str
    subject: str
    body: str
