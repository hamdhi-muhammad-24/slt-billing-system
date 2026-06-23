from itsdangerous import URLSafeTimedSerializer

from app.core.config import settings

_SALT = "pdf-link"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.pdf_token_secret, salt=_SALT)


def mint_pdf_token(invoice_id: int) -> str:
    return _serializer().dumps({"invoice_id": invoice_id})


def verify_pdf_token(token: str) -> dict:
    """Return {"invoice_id": int} or raise BadSignature / SignatureExpired."""
    return _serializer().loads(token, max_age=settings.pdf_token_expire_seconds)
