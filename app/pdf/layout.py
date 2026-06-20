"""
PDF layout constants, colour definitions, page geometry, and drawing helpers.

Import-time side effect: registers Noto fonts with ReportLab's font registry.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = A4          # 595.28 × 841.89 pt
MARGIN     = 36.0
LEFT       = MARGIN
RIGHT      = PAGE_W - MARGIN
CONTENT_W  = RIGHT - LEFT    # ≈ 523 pt

# ---------------------------------------------------------------------------
# Colours (from PDF.md §1)
# ---------------------------------------------------------------------------
HEADER_BLUE  = HexColor("#14529E")
LABEL_BLUE   = HexColor("#2E6DB4")
TEAL_FILL    = HexColor("#16A7C2")
TEAL_BORDER  = HexColor("#16A7C2")
GREEN_BORDER = HexColor("#4CAF50")
BOX_BORDER   = HexColor("#BFC9D4")
TEXT_COLOR   = HexColor("#1A1A1A")
MUTED_COLOR  = HexColor("#6B7280")
RED_COLOR    = HexColor("#CC0000")
LIGHT_GREY   = HexColor("#F4F7FA")
WHITE        = colors.white
BLACK        = colors.black

# ---------------------------------------------------------------------------
# Asset paths
# ---------------------------------------------------------------------------
_ASSETS   = Path(__file__).parent / "assets"
LOGO_PATH = str(_ASSETS / "logo.png")
_FONTS    = _ASSETS / "fonts"

# ---------------------------------------------------------------------------
# Font registration (runs at import time)
# ---------------------------------------------------------------------------
pdfmetrics.registerFont(TTFont("Noto",        str(_FONTS / "NotoSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Noto-Bold",   str(_FONTS / "NotoSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("NotoSinhala", str(_FONTS / "NotoSansSinhala-Regular.ttf")))
pdfmetrics.registerFont(TTFont("NotoTamil",   str(_FONTS / "NotoSansTamil-Regular.ttf")))


# ---------------------------------------------------------------------------
# Drawing helpers (used by renderer.py — keep stateless)
# ---------------------------------------------------------------------------

def hrule(c, x: float, y: float, w: float,
          color: object = BOX_BORDER, lw: float = 0.5) -> None:
    """Draw a horizontal rule."""
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x, y, x + w, y)


def filled_rect(c, x: float, y: float, w: float, h: float,
                fill: object = LIGHT_GREY, stroke: object = BOX_BORDER,
                lw: float = 0.5, radius: float = 0.0) -> None:
    """Filled (and optionally stroked) rectangle or rounded-rect."""
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(lw)
    if radius:
        c.roundRect(x, y, w, h, radius, stroke=1, fill=1)
    else:
        c.rect(x, y, w, h, stroke=1, fill=1)


def outline_rect(c, x: float, y: float, w: float, h: float,
                 stroke: object = BOX_BORDER, lw: float = 0.5) -> None:
    """Border-only rectangle (no fill)."""
    c.setStrokeColor(stroke)
    c.setLineWidth(lw)
    c.setFillColor(WHITE)
    c.rect(x, y, w, h, stroke=1, fill=0)


def draw_field_box(c, label: str, value: str,
                   x: float, y: float, w: float, h: float = 15,
                   label_size: float = 6.5, value_size: float = 9.0,
                   border: object = BOX_BORDER,
                   label_color: object = LABEL_BLUE,
                   fill: object = LIGHT_GREY) -> None:
    """Label above, value inside a filled box."""
    c.setFont("Noto", label_size)
    c.setFillColor(label_color)
    c.drawString(x, y + h + 2.0, label)
    filled_rect(c, x, y, w, h, fill=fill, stroke=border)
    c.setFont("Noto", value_size)
    c.setFillColor(TEXT_COLOR)
    c.drawString(x + 4.0, y + (h - value_size * 0.75) / 2.0, value)
