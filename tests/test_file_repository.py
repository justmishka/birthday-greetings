from datetime import date

from src.adapters.file_repository import FileFriendRepository


SAMPLE_FILE_CONTENT = """\
last_name, first_name, date_of_birth, email
Doe, John, 1982/10/08, john.doe@foobar.com
Ann, Mary, 1975/09/11, mary.ann@foobar.com
"""


class TestFileFriendRepository:
    def test_loads_friends_from_file(self, tmp_path):
        f = tmp_path / "friends.txt"
        f.write_text(SAMPLE_FILE_CONTENT)
        repo = FileFriendRepository(f)
        friends = repo.load_friends()
        assert len(friends) == 2
        assert friends[0].first_name == "John"
        assert friends[0].last_name == "Doe"
        assert friends[0].date_of_birth == date(1982, 10, 8)
        assert friends[0].email == "john.doe@foobar.com"
        assert friends[1].first_name == "Mary"

    def test_handles_whitespace(self, tmp_path):
        content = "last_name, first_name, date_of_birth, email\n  Doe ,  John , 1982/10/08 , john@test.com \n"
        f = tmp_path / "friends.txt"
        f.write_text(content)
        repo = FileFriendRepository(f)
        friends = repo.load_friends()
        assert len(friends) == 1
        assert friends[0].first_name == "John"
        assert friends[0].last_name == "Doe"
        assert friends[0].email == "john@test.com"

    def test_skips_empty_lines(self, tmp_path):
        content = "last_name, first_name, date_of_birth, email\n\nDoe, John, 1982/10/08, john@test.com\n\n"
        f = tmp_path / "friends.txt"
        f.write_text(content)
        repo = FileFriendRepository(f)
        friends = repo.load_friends()
        assert len(friends) == 1

    def test_empty_file_only_header(self, tmp_path):
        f = tmp_path / "friends.txt"
        f.write_text("last_name, first_name, date_of_birth, email\n")
        repo = FileFriendRepository(f)
        assert repo.load_friends() == []

    def test_feb29_date_parsed(self, tmp_path):
        content = "last_name, first_name, date_of_birth, email\nLeap, Larry, 2000/02/29, larry@test.com\n"
        f = tmp_path / "friends.txt"
        f.write_text(content)
        repo = FileFriendRepository(f)
        friends = repo.load_friends()
        assert friends[0].date_of_birth == date(2000, 2, 29)

    def test_skips_malformed_lines(self, tmp_path):
        content = "last_name, first_name, date_of_birth, email\nbad line\nDoe, John, 1982/10/08, john@test.com\n"
        f = tmp_path / "friends.txt"
        f.write_text(content)
        repo = FileFriendRepository(f)
        friends = repo.load_friends()
        assert len(friends) == 1
