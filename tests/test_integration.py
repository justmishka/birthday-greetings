from datetime import date

from src.adapters.file_repository import FileFriendRepository
from src.domain.birthday_service import compose_greeting, compose_reminders, find_birthdays
from src.domain.models import Message
from src.ports.message_sender import MessageSender


class InMemoryMessageSender(MessageSender):
    def __init__(self):
        self.sent: list[Message] = []

    def send(self, message: Message) -> None:
        self.sent.append(message)


FRIENDS_DATA = """\
last_name, first_name, date_of_birth, email
Doe, John, 1982/10/08, john.doe@foobar.com
Ann, Mary, 1975/09/11, mary.ann@foobar.com
Leap, Larry, 2000/02/29, larry.leap@foobar.com
Smith, Bob, 1988/10/08, bob.smith@foobar.com
"""


class TestIntegration:
    def _run(self, tmp_path, today):
        f = tmp_path / "friends.txt"
        f.write_text(FRIENDS_DATA)
        repo = FileFriendRepository(f)
        sender = InMemoryMessageSender()

        friends = repo.load_friends()
        celebrants = find_birthdays(friends, today)

        for celebrant in celebrants:
            sender.send(compose_greeting(celebrant))
        for reminder in compose_reminders(celebrants, friends):
            sender.send(reminder)

        return sender.sent

    def test_single_birthday(self, tmp_path):
        msgs = self._run(tmp_path, date(2026, 9, 11))
        greetings = [m for m in msgs if m.subject == "Happy birthday!"]
        reminders = [m for m in msgs if m.subject == "Birthday Reminder"]
        assert len(greetings) == 1
        assert greetings[0].to == "mary.ann@foobar.com"
        assert "Mary" in greetings[0].body
        assert len(reminders) == 3  # John, Larry, Bob get reminders

    def test_multiple_birthdays_same_day(self, tmp_path):
        msgs = self._run(tmp_path, date(2026, 10, 8))
        greetings = [m for m in msgs if m.subject == "Happy birthday!"]
        reminders = [m for m in msgs if m.subject == "Birthday Reminder"]
        assert len(greetings) == 2  # John + Bob
        assert {g.to for g in greetings} == {"john.doe@foobar.com", "bob.smith@foobar.com"}
        assert len(reminders) == 2  # Mary + Larry get consolidated reminder
        for r in reminders:
            assert "John Doe" in r.body
            assert "Bob Smith" in r.body

    def test_feb29_birthday_on_non_leap_year(self, tmp_path):
        msgs = self._run(tmp_path, date(2025, 2, 28))
        greetings = [m for m in msgs if m.subject == "Happy birthday!"]
        assert len(greetings) == 1
        assert greetings[0].to == "larry.leap@foobar.com"

    def test_feb29_birthday_on_leap_year(self, tmp_path):
        msgs = self._run(tmp_path, date(2024, 2, 29))
        greetings = [m for m in msgs if m.subject == "Happy birthday!"]
        assert len(greetings) == 1
        assert greetings[0].to == "larry.leap@foobar.com"

    def test_no_birthdays_today(self, tmp_path):
        msgs = self._run(tmp_path, date(2026, 1, 1))
        assert msgs == []

    def test_swappable_sender(self, tmp_path):
        """Proves the port/adapter pattern works — InMemoryMessageSender
        is a different adapter than EmailMessageSender, zero code changes."""
        sender = InMemoryMessageSender()
        assert isinstance(sender, MessageSender)
        sender.send(Message(to="test@test.com", subject="Test", body="Hi"))
        assert len(sender.sent) == 1
