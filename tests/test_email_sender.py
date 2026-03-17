from src.adapters.email_sender import EmailMessageSender
from src.domain.models import Message
from src.ports.message_sender import MessageSender


class TestEmailMessageSender:
    def test_implements_message_sender(self):
        sender = EmailMessageSender("localhost", 25, "test@test.com")
        assert isinstance(sender, MessageSender)

    def test_send_formats_email(self, mocker):
        mock_smtp_class = mocker.patch("src.adapters.email_sender.smtplib.SMTP")
        mock_server = mock_smtp_class.return_value.__enter__.return_value

        sender = EmailMessageSender("mail.example.com", 587, "from@example.com")
        msg = Message(to="to@example.com", subject="Test", body="Hello")
        sender.send(msg)

        mock_smtp_class.assert_called_once_with("mail.example.com", 587)
        mock_server.sendmail.assert_called_once()
        call_args = mock_server.sendmail.call_args
        assert call_args[0][0] == "from@example.com"
        assert call_args[0][1] == ["to@example.com"]
        raw_email = call_args[0][2]
        assert "Subject: Test" in raw_email
        assert "Hello" in raw_email
