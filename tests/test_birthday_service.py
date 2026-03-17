from datetime import date

from src.domain.birthday_service import (
    compose_greeting,
    compose_reminders,
    find_birthdays,
    is_birthday,
)
from src.domain.models import Friend


def _friend(first="John", last="Doe", dob="1982-10-08", email="john@test.com"):
    return Friend(last, first, date.fromisoformat(dob), email)


class TestIsBirthday:
    def test_matching_date(self):
        f = _friend(dob="1982-10-08")
        assert is_birthday(f, date(2026, 10, 8))

    def test_different_date(self):
        f = _friend(dob="1982-10-08")
        assert not is_birthday(f, date(2026, 10, 9))

    def test_different_month(self):
        f = _friend(dob="1982-10-08")
        assert not is_birthday(f, date(2026, 11, 8))

    def test_feb29_on_leap_year(self):
        f = _friend(dob="2000-02-29")
        assert is_birthday(f, date(2024, 2, 29))

    def test_feb29_on_non_leap_year_matches_feb28(self):
        f = _friend(dob="2000-02-29")
        assert is_birthday(f, date(2025, 2, 28))

    def test_feb29_on_non_leap_year_not_mar1(self):
        f = _friend(dob="2000-02-29")
        assert not is_birthday(f, date(2025, 3, 1))

    def test_feb28_born_not_affected_by_leap_rule(self):
        f = _friend(dob="1990-02-28")
        assert is_birthday(f, date(2025, 2, 28))

    def test_feb28_born_not_on_feb29(self):
        f = _friend(dob="1990-02-28")
        assert not is_birthday(f, date(2024, 2, 29))

    def test_year_does_not_matter(self):
        f = _friend(dob="1950-03-15")
        assert is_birthday(f, date(2026, 3, 15))


class TestFindBirthdays:
    def test_finds_matching_friends(self):
        john = _friend(first="John", dob="1982-10-08", email="john@test.com")
        mary = _friend(first="Mary", dob="1975-09-11", email="mary@test.com")
        result = find_birthdays([john, mary], date(2026, 10, 8))
        assert result == [john]

    def test_multiple_birthdays_same_day(self):
        a = _friend(first="A", dob="1980-05-01", email="a@test.com")
        b = _friend(first="B", dob="1990-05-01", email="b@test.com")
        result = find_birthdays([a, b], date(2026, 5, 1))
        assert result == [a, b]

    def test_no_birthdays(self):
        f = _friend(dob="1982-10-08")
        assert find_birthdays([f], date(2026, 1, 1)) == []

    def test_empty_list(self):
        assert find_birthdays([], date(2026, 1, 1)) == []


class TestComposeGreeting:
    def test_greeting_message(self):
        f = _friend(first="John", email="john@test.com")
        msg = compose_greeting(f)
        assert msg.to == "john@test.com"
        assert msg.subject == "Happy birthday!"
        assert msg.body == "Happy birthday, dear John!"


class TestComposeReminders:
    def test_single_celebrant(self):
        john = _friend(first="John", last="Doe", dob="1982-10-08", email="john@test.com")
        mary = _friend(first="Mary", last="Ann", dob="1975-09-11", email="mary@test.com")
        msgs = compose_reminders([john], [john, mary])
        assert len(msgs) == 1
        assert msgs[0].to == "mary@test.com"
        assert msgs[0].subject == "Birthday Reminder"
        assert "John Doe" in msgs[0].body
        assert "Dear Mary" in msgs[0].body

    def test_multiple_celebrants_consolidated(self):
        a = _friend(first="A", last="One", dob="1980-05-01", email="a@test.com")
        b = _friend(first="B", last="Two", dob="1990-05-01", email="b@test.com")
        c = _friend(first="C", last="Three", dob="1985-12-25", email="c@test.com")
        msgs = compose_reminders([a, b], [a, b, c])
        assert len(msgs) == 1
        assert msgs[0].to == "c@test.com"
        assert "A One" in msgs[0].body
        assert "B Two" in msgs[0].body

    def test_no_celebrants_no_reminders(self):
        assert compose_reminders([], [_friend()]) == []

    def test_all_friends_are_celebrants_no_reminders(self):
        john = _friend(first="John", email="john@test.com")
        assert compose_reminders([john], [john]) == []

    def test_reminder_sent_to_all_non_celebrants(self):
        john = _friend(first="John", last="Doe", dob="1982-10-08", email="john@test.com")
        mary = _friend(first="Mary", last="Ann", dob="1975-09-11", email="mary@test.com")
        bob = _friend(first="Bob", last="Smith", dob="1988-03-22", email="bob@test.com")
        msgs = compose_reminders([john], [john, mary, bob])
        assert len(msgs) == 2
        recipients = {m.to for m in msgs}
        assert recipients == {"mary@test.com", "bob@test.com"}
