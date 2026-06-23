import enum

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    Integer,
    Text,
    UniqueConstraint,
    func,
)

from app.db.base import Base


class NotificationChannel(enum.Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"


class NotificationStatus(enum.Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    FAILED = "FAILED"


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"
    __table_args__ = (
        UniqueConstraint("invoice_id", "channel", name="uq_outbox_invoice_channel"),
    )

    id           = Column(BigInteger, Identity(always=True), primary_key=True)
    invoice_id   = Column(BigInteger, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    channel      = Column(Enum(NotificationChannel, name="notification_channel"), nullable=False)
    status       = Column(
        Enum(NotificationStatus, name="notification_status"),
        nullable=False,
        server_default="QUEUED",
    )
    recipient    = Column(Text, nullable=False)
    attempts     = Column(Integer, nullable=False, server_default="0")
    last_error   = Column(Text, nullable=True)
    provider_ref = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    sent_at      = Column(DateTime(timezone=True), nullable=True)
