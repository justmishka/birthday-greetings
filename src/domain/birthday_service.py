import calendar
from datetime import date

from src.domain.models import Friend, Message


def is_birthday(friend: Friend, today: date) -> bool:
    born = friend.date_of_birth
    if born.month == 2 and born.day == 29:
        if not calendar.isleap(today.year):
            return today.month == 2 and today.day == 28
    return today.month == born.month and today.day == born.day


def find_birthdays(friends: list[Friend], today: date) -> list[Friend]:
    return [f for f in friends if is_birthday(f, today)]


def compose_greeting(friend: Friend) -> Message:
    return Message(
        to=friend.email,
        subject="Happy birthday!",
        body=f"Happy birthday, dear {friend.first_name}!",
    )


def compose_reminders(
    celebrants: list[Friend],
    all_friends: list[Friend],
) -> list[Message]:
    if not celebrants:
        return []

    non_celebrant_emails = {f.email for f in all_friends} - {c.email for c in celebrants}
    recipients = [f for f in all_friends if f.email in non_celebrant_emails]

    if not recipients:
        return []

    if len(celebrants) == 1:
        c = celebrants[0]
        body_line = (
            f"Today is {c.first_name} {c.last_name}'s birthday. "
            "Don't forget to send him a message!"
        )
    else:
        lines = [
            f"- {c.first_name} {c.last_name}" for c in celebrants
        ]
        body_line = (
            "Today is the birthday of:\n"
            + "\n".join(lines)
            + "\nDon't forget to send them a message!"
        )

    return [
        Message(
            to=r.email,
            subject="Birthday Reminder",
            body=f"Dear {r.first_name},\n\n{body_line}",
        )
        for r in recipients
    ]
