"""Email sender interface + backends."""
from __future__ import annotations

import smtplib
import uuid
from abc import ABC, abstractmethod
from email.message import EmailMessage
from typing import Optional


class EmailSender(ABC):
    @abstractmethod
    def send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: Optional[list[tuple[str, bytes, str]]] = None,
    ) -> str:
        """Send an email and return a provider reference string."""


class SmtpEmailSender(EmailSender):
    def __init__(self) -> None:
        from app.core.config import settings
        self._host = settings.smtp_host
        self._port = settings.smtp_port
        self._from = settings.email_from

    def send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: Optional[list[tuple[str, bytes, str]]] = None,
    ) -> str:
        msg = EmailMessage()
        msg["From"] = self._from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content("This message requires an HTML-capable email client.")
        msg.add_alternative(html, subtype="html")

        if attachments:
            for filename, data, maintype_subtype in attachments:
                maintype, subtype = maintype_subtype.split("/", 1)
                msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

        with smtplib.SMTP(self._host, self._port) as smtp:
            smtp.send_message(msg)

        return f"smtp-{uuid.uuid4().hex}"


class SesEmailSender(EmailSender):
    def send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: Optional[list[tuple[str, bytes, str]]] = None,
    ) -> str:
        raise NotImplementedError("SES wired in Phase 6")


def get_email_sender() -> EmailSender:
    from app.core.config import settings
    backend = settings.email_backend.lower()
    if backend == "smtp":
        return SmtpEmailSender()
    if backend == "ses":
        return SesEmailSender()
    raise ValueError(f"Unknown EMAIL_BACKEND: {backend!r}")
