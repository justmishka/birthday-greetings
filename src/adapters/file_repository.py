from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Union

from src.domain.models import Friend
from src.ports.friend_repository import FriendRepository


class FileFriendRepository(FriendRepository):
    def __init__(self, file_path: Union[str, Path]):
        self._file_path = Path(file_path)

    def load_friends(self) -> list[Friend]:
        friends = []
        text = self._file_path.read_text()
        lines = text.strip().splitlines()

        for line in lines[1:]:  # skip header
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 4:
                continue
            last_name, first_name, dob_str, email = parts
            dob = datetime.strptime(dob_str, "%Y/%m/%d").date()
            friends.append(Friend(last_name, first_name, dob, email))

        return friends
