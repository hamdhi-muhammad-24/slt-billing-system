"""
Barcode and QR code generation helpers.

The renderer draws generated PNGs directly from memory. Tests can call the
make_* helpers to verify real barcode/QR generation without building a PDF.
"""
from __future__ import annotations

import io

from reportlab.lib.utils import ImageReader


def make_barcode_png(text: str) -> bytes:
    """Return Code-128 barcode PNG bytes for text."""
    if not text:
        raise ValueError("barcode text cannot be empty")

    from barcode import Code128
    from barcode.writer import ImageWriter

    buf = io.BytesIO()
    code = Code128(text, writer=ImageWriter())
    code.write(buf, options={
        "write_text": False,
        "dpi": 120,
        "module_width": 0.25,
        "module_height": 7.0,
        "quiet_zone": 1.5,
    })
    return buf.getvalue()


def make_qr_png(data: str) -> bytes:
    """Return QR code PNG bytes for data."""
    if not data:
        raise ValueError("QR data cannot be empty")

    import qrcode

    buf = io.BytesIO()
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(buf, format="PNG")
    return buf.getvalue()


def draw_barcode(
    c,
    text: str,
    x: float,
    y: float,
    w: float = 170.0,
    h: float = 25.0,
    strict: bool = False,
) -> bool:
    """Draw a Code-128 barcode and return True when a real barcode rendered."""
    try:
        c.drawImage(
            ImageReader(io.BytesIO(make_barcode_png(text))),
            x,
            y,
            width=w,
            height=h,
            mask="auto",
        )
        return True
    except Exception:
        if strict:
            raise
        from app.pdf.layout import BOX_BORDER, TEXT_COLOR

        c.setStrokeColor(BOX_BORDER)
        c.setLineWidth(0.5)
        c.rect(x, y, w, h)
        c.setFont("Noto", 6)
        c.setFillColor(TEXT_COLOR)
        c.drawString(x + 4, y + 4, f"CODE-128: {text}")
        return False


def draw_qr(
    c,
    data: str,
    x: float,
    y: float,
    size: float = 48.0,
    strict: bool = False,
) -> bool:
    """Draw a QR code and return True when a real QR rendered."""
    try:
        c.drawImage(
            ImageReader(io.BytesIO(make_qr_png(data))),
            x,
            y,
            width=size,
            height=size,
            mask="auto",
        )
        return True
    except Exception:
        if strict:
            raise
        from app.pdf.layout import BOX_BORDER, TEXT_COLOR

        c.setStrokeColor(BOX_BORDER)
        c.setLineWidth(0.5)
        c.rect(x, y, size, size)
        c.setFont("Noto", 5)
        c.setFillColor(TEXT_COLOR)
        c.drawString(x + 2, y + 2, "QR")
        return False
