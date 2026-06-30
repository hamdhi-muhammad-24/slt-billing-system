from __future__ import annotations

import pytest

from app.pdf.barcodes import make_barcode_png, make_qr_png


def test_code128_barcode_png_is_generated() -> None:
    data = make_barcode_png("0016869532-2488")
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(data) > 100


def test_qr_png_is_generated() -> None:
    data = make_qr_png("https://www.slt.lk/payonline?inv=0016869532-2488")
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(data) > 100


def test_empty_barcode_payload_is_rejected() -> None:
    with pytest.raises(ValueError):
        make_barcode_png("")


def test_empty_qr_payload_is_rejected() -> None:
    with pytest.raises(ValueError):
        make_qr_png("")
