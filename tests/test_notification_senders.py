"""Unit tests for notification senders — no network, no DB."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from app.notifications.senders.email import (
    EmailSender,
    SmtpEmailSender,
    SesEmailSender,
    get_email_sender,
)
from app.notifications.senders.sms import (
    SmsSender,
    ConsoleSmsSender,
    TwilioSmsSender,
    get_sms_sender,
)


# ---------------------------------------------------------------------------
# Fake backends that record calls (no network)
# ---------------------------------------------------------------------------

class FakeEmailSender(EmailSender):
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: Optional[list[tuple[str, bytes, str]]] = None,
    ) -> str:
        ref = f"fake-email-{len(self.calls)}"
        self.calls.append({"to": to, "subject": subject, "html": html,
                           "attachments": attachments, "ref": ref})
        return ref


class FakeSmsSender(SmsSender):
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send(self, to: str, body: str) -> str:
        ref = f"fake-sms-{len(self.calls)}"
        self.calls.append({"to": to, "body": body, "ref": ref})
        return ref


# ---------------------------------------------------------------------------
# FakeSender behaviour
# ---------------------------------------------------------------------------

def test_fake_email_sender_records_call():
    sender = FakeEmailSender()
    ref = sender.send("user@example.com", "Test subject", "<p>hello</p>")
    assert ref == "fake-email-0"
    assert len(sender.calls) == 1
    assert sender.calls[0]["to"] == "user@example.com"
    assert sender.calls[0]["subject"] == "Test subject"


def test_fake_sms_sender_records_call():
    sender = FakeSmsSender()
    ref = sender.send("+94771234567", "Your bill is ready")
    assert ref == "fake-sms-0"
    assert len(sender.calls) == 1
    assert sender.calls[0]["to"] == "+94771234567"
    assert sender.calls[0]["body"] == "Your bill is ready"


# ---------------------------------------------------------------------------
# Factory — correct class per env var
# ---------------------------------------------------------------------------

def test_get_email_sender_returns_smtp(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.email_backend", "smtp")
    sender = get_email_sender()
    assert isinstance(sender, SmtpEmailSender)


def test_get_email_sender_returns_ses(monkeypatch):
    import sys
    monkeypatch.setattr("app.core.config.settings.email_backend", "ses")
    monkeypatch.setattr("app.core.config.settings.aws_region", "ap-southeast-1")
    fake_boto3 = MagicMock()
    with patch.dict(sys.modules, {"boto3": fake_boto3}):
        sender = get_email_sender()
    assert isinstance(sender, SesEmailSender)


def test_get_email_sender_unknown_raises(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.email_backend", "sendgrid")
    with pytest.raises(ValueError, match="EMAIL_BACKEND"):
        get_email_sender()


def test_get_sms_sender_returns_console(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.sms_backend", "console")
    sender = get_sms_sender()
    assert isinstance(sender, ConsoleSmsSender)


def test_get_sms_sender_returns_twilio(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.sms_backend", "twilio")
    sender = get_sms_sender()
    assert isinstance(sender, TwilioSmsSender)


def test_get_sms_sender_unknown_raises(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.sms_backend", "sns")
    with pytest.raises(ValueError, match="SMS_BACKEND"):
        get_sms_sender()


# ---------------------------------------------------------------------------
# ConsoleSmsSender — returns a ref, records
# ---------------------------------------------------------------------------

def test_console_sms_sender_returns_ref():
    sender = ConsoleSmsSender()
    ref = sender.send("+94770000001", "Hello")
    assert ref.startswith("console-")
    assert len(ref) > len("console-")


def test_console_sms_sender_different_refs():
    sender = ConsoleSmsSender()
    ref1 = sender.send("+94770000001", "msg1")
    ref2 = sender.send("+94770000002", "msg2")
    assert ref1 != ref2


# ---------------------------------------------------------------------------
# SesEmailSender — calls boto3 send_raw_email with correct parameters
# ---------------------------------------------------------------------------

def test_ses_sender_sends_via_boto3(monkeypatch):
    import sys
    monkeypatch.setattr("app.core.config.settings.aws_region", "ap-southeast-1")
    monkeypatch.setattr("app.core.config.settings.email_from", "billing@slt.lk")

    mock_ses_client = MagicMock()
    mock_ses_client.send_raw_email.return_value = {"MessageId": "ses-abc123"}
    fake_boto3 = MagicMock()
    fake_boto3.client.return_value = mock_ses_client

    with patch.dict(sys.modules, {"boto3": fake_boto3}):
        sender = SesEmailSender()
        ref = sender.send("user@example.com", "Test subject", "<p>hello</p>")

    assert ref == "ses-abc123"
    mock_ses_client.send_raw_email.assert_called_once()
    call_kwargs = mock_ses_client.send_raw_email.call_args[1]
    assert call_kwargs["Source"] == "billing@slt.lk"
    assert "user@example.com" in call_kwargs["Destinations"]


# ---------------------------------------------------------------------------
# SmtpEmailSender — builds correct MIME message, no socket opened
# ---------------------------------------------------------------------------

def test_smtp_sender_builds_correct_message(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.smtp_host", "localhost")
    monkeypatch.setattr("app.core.config.settings.smtp_port", 1025)
    monkeypatch.setattr("app.core.config.settings.email_from", "billing@slt.lk")

    captured: list[EmailMessage] = []

    class FakeSMTP:
        def __init__(self, host, port):
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def send_message(self, msg):
            captured.append(msg)

    with patch("smtplib.SMTP", FakeSMTP):
        sender = SmtpEmailSender()
        ref = sender.send(
            to="customer@example.com",
            subject="Your SLT bill",
            html="<p>Amount: Rs 4628.52</p>",
        )

    assert ref.startswith("smtp-")
    assert len(captured) == 1
    msg = captured[0]
    assert msg["From"] == "billing@slt.lk"
    assert msg["To"] == "customer@example.com"
    assert msg["Subject"] == "Your SLT bill"


def test_smtp_sender_with_attachment(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.smtp_host", "localhost")
    monkeypatch.setattr("app.core.config.settings.smtp_port", 1025)
    monkeypatch.setattr("app.core.config.settings.email_from", "billing@slt.lk")

    captured: list[EmailMessage] = []

    class FakeSMTP:
        def __init__(self, host, port): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def send_message(self, msg): captured.append(msg)

    pdf_bytes = b"%PDF-fake"
    with patch("smtplib.SMTP", FakeSMTP):
        sender = SmtpEmailSender()
        ref = sender.send(
            to="customer@example.com",
            subject="Bill with PDF",
            html="<p>See attached</p>",
            attachments=[("bill.pdf", pdf_bytes, "application/pdf")],
        )

    assert ref.startswith("smtp-")
    assert len(captured) == 1
    # Message should be multipart when an attachment is present
    msg = captured[0]
    assert msg.is_multipart()


def test_smtp_sender_no_socket_without_patch():
    """Confirm that calling SmtpEmailSender.send without the patch would fail
    (i.e., the patch in the tests above is actually suppressing the socket).
    This test verifies that the real smtplib.SMTP raises on a bad port."""
    import socket
    sender = SmtpEmailSender.__new__(SmtpEmailSender)
    sender._host = "127.0.0.1"
    sender._port = 19999  # nothing listening here
    sender._from = "test@slt.lk"
    with pytest.raises((ConnectionRefusedError, OSError, socket.error)):
        sender.send("x@example.com", "subj", "<p>body</p>")
