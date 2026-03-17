import smtplib
from email.mime.text import MIMEText

from src.domain.models import Message
from src.ports.message_sender import MessageSender


class EmailMessageSender(MessageSender):
    def __init__(self, smtp_host: str, smtp_port: int, from_addr: str):
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._from_addr = from_addr

    def send(self, message: Message) -> None:
        msg = MIMEText(message.body)
        msg["Subject"] = message.subject
        msg["From"] = self._from_addr
        msg["To"] = message.to

        with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
            server.sendmail(self._from_addr, [message.to], msg.as_string())
