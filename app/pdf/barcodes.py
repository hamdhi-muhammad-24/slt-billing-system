"""
Barcode and QR code generation helpers.

Both functions render their output into a BytesIO buffer and draw it onto the
canvas via drawImage so no temporary files are created on disk.
"""
from __future__ import annotations

import io

from reportlab.lib.utils import ImageReader


def draw_barcode(c, text: str,
                 x: float, y: float,
                 w: float = 170.0, h: float = 25.0) -> None:
    """Draw a Code-128 barcode at (x, y) with size (w × h) points."""
    buf = io.BytesIO()
    try:
        from barcode import Code128
        from barcode.writer import ImageWriter

        code = Code128(text, writer=ImageWriter())
        code.write(buf, options={
            "write_text": False,
            "dpi": 120,
            "module_width": 0.25,
            "module_height": 7.0,
            "quiet_zone": 1.5,
        })
        buf.seek(0)
        c.drawImage(ImageReader(buf), x, y, width=w, height=h, mask="auto")
    except Exception:
        # Fallback: labelled placeholder box so the PDF still renders
        from app.pdf.layout import BOX_BORDER, TEXT_COLOR
        c.setStrokeColor(BOX_BORDER)
        c.setLineWidth(0.5)
        c.rect(x, y, w, h)
        c.setFont("Noto", 6)
        c.setFillColor(TEXT_COLOR)
        c.drawString(x + 4, y + 4, f"CODE-128: {text}")


def draw_qr(c, data: str,
            x: float, y: float,
            size: float = 48.0) -> None:
    """Draw a QR code at (x, y) with square side size points."""
    buf = io.BytesIO()
    try:
        import qrcode

        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(buf, format="PNG")
        buf.seek(0)
        c.drawImage(ImageReader(buf), x, y, width=size, height=size, mask="auto")
    except Exception:
        from app.pdf.layout import BOX_BORDER, TEXT_COLOR
        c.setStrokeColor(BOX_BORDER)
        c.setLineWidth(0.5)
        c.rect(x, y, size, size)
        c.setFont("Noto", 5)
        c.setFillColor(TEXT_COLOR)
        c.drawString(x + 2, y + 2, "QR")
