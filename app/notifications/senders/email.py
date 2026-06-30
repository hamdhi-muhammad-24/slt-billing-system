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
    def __init__(self) -> None:
        import boto3
        from app.core.config import settings
        self._client = boto3.client("ses", region_name=settings.aws_region)
        self._from = settings.email_from

    def send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: Optional[list[tuple[str, bytes, str]]] = None,
    ) -> str:
        from email import encoders
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("mixed")
        msg["From"] = self._from
        msg["To"] = to
        msg["Subject"] = subject

        body = MIMEMultipart("alternative")
        body.attach(MIMEText("This message requires an HTML-capable email client.", "plain"))
        body.attach(MIMEText(html, "html"))
        msg.attach(body)

        if attachments:
            for filename, data, maintype_subtype in attachments:
                maintype, subtype = maintype_subtype.split("/", 1)
                part = MIMEBase(maintype, subtype)
                part.set_payload(data)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(part)

        response = self._client.send_raw_email(
            Source=self._from,
            Destinations=[to],
            RawMessage={"Data": msg.as_string()},
        )
        return response["MessageId"]


def get_email_sender() -> EmailSender:
    from app.core.config import settings
    backend = settings.email_backend.lower()
    if backend == "smtp":
        return SmtpEmailSender()
    if backend == "ses":
        return SesEmailSender()
    raise ValueError(f"Unknown EMAIL_BACKEND: {backend!r}")
