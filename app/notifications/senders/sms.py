"""SMS sender interface + backends."""
from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SmsSender(ABC):
    @abstractmethod
    def send(self, to: str, body: str) -> str:
        """Send an SMS and return a provider reference string."""


class TwilioSmsSender(SmsSender):
    def __init__(self) -> None:
        from app.core.config import settings
        self._account_sid = settings.twilio_account_sid
        self._auth_token = settings.twilio_auth_token
        self._from = settings.twilio_from

    def send(self, to: str, body: str) -> str:
        # Lazy import so this module loads fine without the twilio package installed
        from twilio.rest import Client  # type: ignore[import]

        client = Client(self._account_sid, self._auth_token)
        message = client.messages.create(body=body, from_=self._from, to=to)
        return message.sid


class ConsoleSmsSender(SmsSender):
    def send(self, to: str, body: str) -> str:
        ref = f"console-{uuid.uuid4().hex}"
        logger.info("SMS [%s] to=%s body=%r", ref, to, body)
        return ref


def get_sms_sender() -> SmsSender:
    from app.core.config import settings
    backend = settings.sms_backend.lower()
    if backend == "console":
        return ConsoleSmsSender()
    if backend == "twilio":
        return TwilioSmsSender()
    raise ValueError(f"Unknown SMS_BACKEND: {backend!r}")
