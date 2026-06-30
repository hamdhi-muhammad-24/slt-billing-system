"""S3 storage helper — upload PDFs, generate pre-signed download URLs."""
from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)


def _client():
    import boto3
    from app.core.config import settings
    return boto3.client("s3", region_name=settings.aws_region)


def upload_pdf(key: str, data: bytes) -> str:
    """Upload *data* to the configured S3 bucket under *key*.

    Returns the S3 URI (s3://bucket/key).
    """
    from app.core.config import settings
    _client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType="application/pdf",
    )
    uri = f"s3://{settings.s3_bucket}/{key}"
    log.info("Uploaded PDF to %s", uri)
    return uri


def presign_pdf(key: str, expires: int = 300) -> str:
    """Return a pre-signed HTTPS URL for *key*, valid for *expires* seconds."""
    from app.core.config import settings
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires,
    )


def download_pdf(key: str) -> bytes:
    """Download and return the raw bytes for *key* from S3."""
    from app.core.config import settings
    response = _client().get_object(Bucket=settings.s3_bucket, Key=key)
    return response["Body"].read()
