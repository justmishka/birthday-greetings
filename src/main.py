from __future__ import annotations

import sys
from datetime import date, datetime

from src.adapters.email_sender import EmailMessageSender
from src.adapters.file_repository import FileFriendRepository
from src.domain.birthday_service import compose_greeting, compose_reminders, find_birthdays


def run(
    file_path: str,
    today: date,
    smtp_host: str = "localhost",
    smtp_port: int = 25,
    from_addr: str = "birthdays@example.com",
) -> None:
    repo = FileFriendRepository(file_path)
    sender = EmailMessageSender(smtp_host, smtp_port, from_addr)

    friends = repo.load_friends()
    celebrants = find_birthdays(friends, today)

    for celebrant in celebrants:
        sender.send(compose_greeting(celebrant))

    for reminder in compose_reminders(celebrants, friends):
        sender.send(reminder)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <friends_file> [YYYY-MM-DD]")
        sys.exit(1)

    file_path = sys.argv[1]
    if len(sys.argv) >= 3:
        today = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
    else:
        today = date.today()

    run(file_path, today)
    print(f"Birthday greetings processed for {today}")


if __name__ == "__main__":
    main()
