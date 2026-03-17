from datetime import date

from src.web import _esc, _render_results, _render_friends_table, _friends_to_json, _friends_from_json
from src.domain.models import Friend, Message


class TestEscape:
    def test_escapes_html(self):
        assert _esc('<script>alert("xss")</script>') == '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'

    def test_plain_text_unchanged(self):
        assert _esc("Hello World") == "Hello World"

    def test_ampersand(self):
        assert _esc("A & B") == "A &amp; B"


class TestRenderResults:
    def test_no_messages(self):
        html = _render_results([], 10, 8)
        assert "No birthdays" in html
        assert "October 8" in html

    def test_greeting_rendered(self):
        msgs = [Message(to="john@test.com", subject="Happy birthday!", body="Happy birthday, dear John!")]
        html = _render_results(msgs, 10, 8)
        assert "john@test.com" in html
        assert "Happy birthday, dear John!" in html
        assert "Greeting" in html
        assert "October 8" in html

    def test_reminder_rendered(self):
        msgs = [Message(to="mary@test.com", subject="Birthday Reminder", body="Dear Mary,\n\nToday is John Doe's birthday.")]
        html = _render_results(msgs, 10, 8)
        assert "mary@test.com" in html
        assert "Reminder" in html
        assert "John Doe" in html

    def test_mixed_greetings_and_reminders(self):
        msgs = [
            Message(to="john@test.com", subject="Happy birthday!", body="Happy birthday, dear John!"),
            Message(to="mary@test.com", subject="Birthday Reminder", body="Dear Mary,\n\nToday is John's birthday."),
        ]
        html = _render_results(msgs, 10, 8)
        assert "1 greeting(s)" in html
        assert "1 reminder(s)" in html

    def test_xss_in_message_escaped(self):
        msgs = [Message(to="<script>", subject="Happy birthday!", body="<img onerror=alert(1)>")]
        html = _render_results(msgs, 1, 1)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestFriendsTable:
    def test_empty_list(self):
        html = _render_friends_table([])
        assert "No friends added" in html

    def test_renders_friends(self):
        friends = [
            Friend("Doe", "John", date(1982, 10, 8), "john@test.com"),
            Friend("Ann", "Mary", date(1975, 9, 11), "mary@test.com"),
        ]
        html = _render_friends_table(friends)
        assert "John Doe" in html
        assert "Mary Ann" in html
        assert "October 8" in html
        assert "September 11" in html
        assert "john@test.com" in html
        assert "2 friend(s)" in html

    def test_remove_button_per_friend(self):
        friends = [Friend("Doe", "John", date(1982, 10, 8), "john@test.com")]
        html = _render_friends_table(friends)
        assert "Remove" in html


class TestFriendsJson:
    def test_roundtrip(self):
        friends = [
            Friend("Doe", "John", date(1982, 10, 8), "john@test.com"),
            Friend("Ann", "Mary", date(1975, 9, 11), "mary@test.com"),
        ]
        json_str = _friends_to_json(friends)
        result = _friends_from_json(json_str)
        assert len(result) == 2
        assert result[0].first_name == "John"
        assert result[1].email == "mary@test.com"

    def test_invalid_json(self):
        assert _friends_from_json("not json") == []

    def test_empty(self):
        assert _friends_from_json("[]") == []
