"""
PDF renderer for the SLT E-Bill INVOICE layout.
Accepts a validated Bill object; never reads from the DB directly.

Matches the real SLT sample-1 invoice layout as closely as possible.
Payment slip + legal notice + notice box live in _SlipFlowable (last story
item) so they always anchor to the very bottom of the last page.
"""
from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    NextPageTemplate,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfgen import canvas as rl_canvas

from app.billing.schemas import Bill
from app.pdf import layout as L
from app.pdf.barcodes import draw_barcode, draw_qr

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_amount(d: Decimal) -> str:
    return f"{d:,.2f}"

def _fmt_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")

def _fmt_datetime(d) -> str:
    return d.strftime("%d/%m/%Y %H:%M") if d else ""

def _period_str(s: date | None, e: date | None) -> str:
    return f"{_fmt_date(s)} - {_fmt_date(e)}" if s and e else ""


# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = A4          # 595.28 × 841.89 pt
MARGIN    = L.MARGIN         # 36
LEFT      = L.LEFT           # 36
RIGHT     = L.RIGHT          # 559.28
CONTENT_W = L.CONTENT_W      # 523.28

HEADER_H = 79.0
SLIM_H   = 30.0
REF_W_PX = 1080.0
REF_H_PX = 1528.0
PX_X = PAGE_W / REF_W_PX
PX_Y = PAGE_H / REF_H_PX

# Extra colours used only in the renderer
_MAGENTA       = HexColor("#E21E6A")
_APP_BLUE      = HexColor("#3B58A8")
_PAY_GREEN     = HexColor("#22A555")
_SLIP_LABEL    = HexColor("#C7D8EC")
_SLIP_BORDER   = HexColor("#82A9B8")
_NOTICE_FILL   = HexColor("#FFF5F5")
_NOTICE_RED    = HexColor("#E1272A")
_LEGAL_BLUE    = HexColor("#506982")


def _px(x: float) -> float:
    return x * PX_X


def _py(y_from_top: float) -> float:
    return PAGE_H - y_from_top * PX_Y


def _hpx(h: float) -> float:
    return h * PX_Y


def _wpx(w: float) -> float:
    return w * PX_X


def _fit_text(
    c: rl_canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_w: float,
    font: str = "Noto",
    size: float = 8.0,
    min_size: float = 5.0,
) -> None:
    """Draw text, shrinking it only when needed to keep the SLT boxes tidy."""
    text = text or ""
    draw_size = size
    while draw_size > min_size and c.stringWidth(text, font, draw_size) > max_w:
        draw_size -= 0.25
    c.setFont(font, draw_size)
    c.drawString(x, y, text)


def _ref_line(bill: Bill) -> str:
    return f"{bill.invoice_number}_1-1-02-1-LKR-101-1-BILL-RED_1.1_12:19:536426"


# ---------------------------------------------------------------------------
# NumberedCanvas — defers showPage so "Page X of N" can be painted last
# ---------------------------------------------------------------------------
class _NumberedCanvas(rl_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved: list[dict] = []

    def showPage(self) -> None:
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        n = len(self._saved)
        for i, state in enumerate(self._saved):
            self.__dict__.update(state)
            _paint_page_number(self, i + 1, n)
            super().showPage()
        super().save()


def _paint_page_number(c: rl_canvas.Canvas, page: int, total: int) -> None:
    text = f"{page} of {total}"
    c.setFont("Noto", 7.5)
    if page == 1:
        c.setFillColor(L.MUTED_COLOR)
        c.drawRightString(RIGHT, PAGE_H - HEADER_H - 10, text)
    else:
        c.setFillColor(L.WHITE)
        c.drawRightString(RIGHT - 5, PAGE_H - SLIM_H + 10, text)


# ---------------------------------------------------------------------------
# A. Full header band (page 1)
# ---------------------------------------------------------------------------
def _draw_header(c: rl_canvas.Canvas) -> None:
    y = PAGE_H - HEADER_H
    c.setFillColor(L.HEADER_BLUE)
    c.rect(0, y, PAGE_W, HEADER_H, stroke=0, fill=1)

    # "INVOICE" + company info
    c.setFont("Noto-Bold", 24.5)
    c.setFillColor(L.WHITE)
    c.drawString(LEFT, y + 28, "INVOICE")

    c.setFont("Noto-Bold", 11.5)
    c.drawString(LEFT + 130, y + 42, "Sri Lanka Telecom PLC")
    c.setFont("Noto", 8)
    c.drawString(LEFT + 130, y + 32, "Lotus Road, P.O Box 503, Colombo 01.")

    # SLT MOBITEL logo — right side, preserving aspect ratio, no background
    logo_h = _hpx(88)
    logo_w = _wpx(250)
    try:
        c.drawImage(
            L.LOGO_PATH,
            PAGE_W - _wpx(40) - logo_w, y + _hpx(26),
            width=logo_w, height=logo_h,
            preserveAspectRatio=True, anchor="c", mask="auto",
        )
    except Exception:
        c.setFont("Noto-Bold", 11)
        c.setFillColor(L.WHITE)
        c.drawRightString(RIGHT, y + 30, "SLT MOBITEL")


# ---------------------------------------------------------------------------
# Slim header (continuation pages)
# ---------------------------------------------------------------------------
def _draw_slim_header(c: rl_canvas.Canvas) -> None:
    y = PAGE_H - SLIM_H
    c.setFillColor(L.HEADER_BLUE)
    c.rect(0, y, PAGE_W, SLIM_H, stroke=0, fill=1)

    c.setFont("Noto-Bold", 9)
    c.setFillColor(L.WHITE)
    c.drawString(LEFT, y + 10, "INVOICE — Continued")

    try:
        c.drawImage(L.LOGO_PATH, RIGHT - 72, y + 3,
                    width=72, height=22,
                    preserveAspectRatio=True, anchor="c", mask="auto")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# B. Identity block
# ---------------------------------------------------------------------------
def _draw_identity(c: rl_canvas.Canvas, bill: Bill, top_y: float) -> float:
    """Draw identity block; return y below it (= top of summary section)."""

    left_w   = _wpx(382)
    right_x  = _px(482)
    right_w  = RIGHT - right_x

    # Split right column into inner content column + narrow QR/app column
    _QR_W   = _wpx(124)
    inner_w = _wpx(388)
    qr_x    = _px(887)

    y = top_y - _hpx(61)  # left-column cursor

    # ── Left column ──────────────────────────────────────────────────────
    c.setFont("Noto-Bold", 10.5)
    c.setFillColor(L.LABEL_BLUE)
    c.drawString(LEFT, y, "TELEPHONE NUMBER")
    c.setFont("Noto", 8.5)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT + 140, y, bill.telephone_number or "")
    y -= 6

    ROW_H = 24.0
    ROW_G = 6.0
    LABEL_W = 88.0

    def left_field(label: str, value: str) -> None:
        nonlocal y
        y -= ROW_H + ROW_G
        c.setFont("Noto", 9)
        c.setFillColor(L.LABEL_BLUE)
        c.drawString(LEFT, y + 8, label)
        c.setFillColor(L.WHITE)
        c.setStrokeColor(L.BOX_BORDER)
        c.setLineWidth(0.8)
        c.roundRect(LEFT + LABEL_W, y, left_w - LABEL_W, ROW_H, 4, stroke=1, fill=1)
        c.setFillColor(L.TEXT_COLOR)
        _fit_text(c, value, LEFT + LABEL_W + 10, y + 8, left_w - LABEL_W - 20, "Noto", 8.5)

    left_field("Account Number", bill.account_number)
    left_field("Invoice Number",  bill.invoice_number)
    left_field("Billing Date",    _fmt_date(bill.billing_date))
    left_field("Billing Period",  _period_str(bill.period_start, bill.period_end))
    bottom_left = y   # bottom of left column

    # ── Inner right column ────────────────────────────────────────────────
    ry = top_y - _hpx(53)   # inner-column cursor (page y, counts down)

    # Customer address box (green border)
    cust_h = _hpx(180)
    ry -= cust_h
    c.setStrokeColor(L.GREEN_BORDER)
    c.setLineWidth(0.9)
    c.setFillColor(L.WHITE)
    c.roundRect(right_x, ry, inner_w, cust_h, 10, stroke=1, fill=1)

    c.setFont("Noto-Bold", 7.6)
    c.setFillColor(L.TEXT_COLOR)
    _fit_text(c, "Rev./Mr./Mrs.", right_x + 15, ry + cust_h - 18, inner_w - 30, "Noto-Bold", 7.6)
    _fit_text(c, bill.customer_name, right_x + 15, ry + cust_h - 42, inner_w - 30, "Noto-Bold", 7.6)
    c.setFont("Noto-Bold", 7.3)
    addr_y = ry + cust_h - 55
    for line in bill.address_lines:
        _fit_text(c, line, right_x + 15, addr_y, inner_w - 30, "Noto-Bold", 7.3)
        addr_y -= 11

    # Barcode (invoice number) inside the lower-right of the customer box.
    draw_barcode(c, bill.invoice_number, right_x + inner_w - 96, ry + 7, w=88, h=18)

    # Service-label banner
    ry -= 6
    banner_h = _hpx(42)
    ry -= banner_h
    c.setFillColor(L.TEAL_FILL)
    c.roundRect(right_x, ry, inner_w, banner_h, 3, stroke=0, fill=1)
    c.setFont("Noto", 13)
    c.setFillColor(L.BLACK)
    c.drawCentredString(right_x + inner_w / 2, ry + 6, bill.customer_segment.upper())

    # Reference line (invoice ref + service tag) — small muted text
    ry -= 8
    c.setFont("Noto", 5.2)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(right_x + 7, ry, _ref_line(bill))
    ry -= 9
    c.drawString(right_x + 7, ry, bill.service_label or "SLT Mega Lines")
    inner_bottom = ry - 4   # lowest point of inner column

    # ── QR / MySLT column ─────────────────────────────────────────────────
    # "X of N" is painted by _NumberedCanvas at page y ≈ top_y - 10;
    # start the QR box 14 pt below that to leave it clear.
    qry = top_y - _hpx(30)

    # QR code in amber rounded box
    qr_box = _hpx(122)
    qry -= qr_box
    c.setFillColor(_MAGENTA)
    c.roundRect(qr_x, qry, _QR_W, qr_box, 11, stroke=0, fill=1)
    c.setFillColor(L.WHITE)
    c.roundRect(qr_x + 8, qry + 8, _QR_W - 16, qr_box - 16, 3, stroke=0, fill=1)
    draw_qr(
        c,
        f"https://www.slt.lk/payonline?inv={bill.invoice_number}",
        qr_x + 11, qry + 11, size=qr_box - 22,
    )

    # MySLT app icon in purple rounded box
    qry -= 7
    app_h = _hpx(110)
    qry -= app_h
    c.setFillColor(_APP_BLUE)
    c.roundRect(qr_x, qry, _QR_W, app_h, 11, stroke=0, fill=1)
    c.setFillColor(L.WHITE)
    c.roundRect(qr_x + 9, qry + 18, _QR_W - 18, app_h - 24, 7, stroke=0, fill=1)
    c.setStrokeColor(L.TEAL_FILL)
    c.setLineWidth(3)
    c.line(qr_x + 25, qry + 28, qr_x + 34, qry + 43)
    c.setStrokeColor(L.GREEN_BORDER)
    c.line(qr_x + 39, qry + 27, qr_x + 48, qry + 42)
    c.setStrokeColor(L.HEADER_BLUE)
    c.line(qr_x + 19, qry + 25, qr_x + 27, qry + 37)
    c.setFont("Noto-Bold", 7.5)
    c.setFillColor(L.WHITE)
    c.drawCentredString(qr_x + _QR_W / 2, qry + 8, "MYSLT")

    # Small "www" label under MySLT box
    qry -= 5
    badge_h = 18.0
    qry -= badge_h
    c.setFillColor(_PAY_GREEN)
    c.roundRect(qr_x, qry, _QR_W, badge_h, 10, stroke=0, fill=1)
    c.setFont("Noto-Bold", 6.5)
    c.setFillColor(L.WHITE)
    c.drawCentredString(qr_x + _QR_W / 2 + 5, qry + 10, "www.slt.lk/")
    c.drawCentredString(qr_x + _QR_W / 2 + 5, qry + 3, "payonline")
    c.circle(qr_x + 10, qry + 9, 5, stroke=1, fill=0)
    qr_bottom = qry

    return min(bottom_left, inner_bottom, qr_bottom) - 8


# ---------------------------------------------------------------------------
# C. Summary of Invoice
# ---------------------------------------------------------------------------
def _draw_summary(c: rl_canvas.Canvas, bill: Bill, top_y: float) -> float:
    """Draw 5-box summary row; return y below it."""
    y = top_y - 4
    # Section heading + rule
    c.setFont("Noto-Bold", 11.3)
    c.setFillColor(L.LABEL_BLUE)
    c.drawString(LEFT, y, "SUMMARY OF INVOICE")
    rule_x = LEFT + c.stringWidth("SUMMARY OF INVOICE", "Noto-Bold", 11.3) + 7
    L.hrule(c, rule_x, y + 3, RIGHT - rule_x, color=L.LABEL_BLUE, lw=0.6)
    y -= 9

    BOX_H = _hpx(108)
    OP_W  = _wpx(35)
    box_w = (CONTENT_W - 4 * OP_W) / 5.0

    boxes = [
        ("ශේෂය ගෙන එන", "மு.தொ.நிலுவை", "Balance B/F", _fmt_amount(bill.summary.balance_bf), False),
        ("මුදල් ලැබීම්", "கிடைத்த கொடுப்பனவு", "Payments received", _fmt_amount(bill.summary.payments_received), False),
        ("කාලසීමාවට අයකිරීම්", "காலப்பகுதிக்கான கட்டணம்", "Charges for the period", _fmt_amount(bill.summary.charges_for_period), False),
        ("ගෙවිය යුතු මුදල", "செலுத்த வேண்டிய தொகை", "Total payable", _fmt_amount(bill.summary.total_payable), True),
        ("ගෙවීම කල යුතු දිනය", "செலுத்த வேண்டிய தினம்", "Payment due date", _fmt_date(bill.due_date), True),
    ]
    operators = ["-", "+", "="]

    y -= BOX_H
    bx = LEFT
    for i, (si, ta, en, val, teal) in enumerate(boxes):
        c.setFillColor(L.WHITE)
        c.setStrokeColor(L.TEAL_BORDER)
        c.setLineWidth(0.9)
        c.roundRect(bx, y, box_w, BOX_H, 9, stroke=1, fill=1)

        caption_h = _hpx(61)
        if teal:
            c.setFillColor(L.TEAL_FILL)
            c.roundRect(bx, y + BOX_H - caption_h, box_w, caption_h, 9, stroke=0, fill=1)
            c.rect(bx, y + BOX_H - caption_h, box_w, caption_h / 2, stroke=0, fill=1)
            label_color = L.WHITE
        else:
            c.setStrokeColor(L.TEAL_BORDER)
            c.line(bx, y + _hpx(43), bx + box_w, y + _hpx(43))
            label_color = L.LABEL_BLUE

        c.setFillColor(label_color)
        c.setFont("NotoSinhala", 4.9)
        c.drawCentredString(bx + box_w / 2, y + BOX_H - _hpx(20), si)
        c.setFont("NotoTamil", 4.6)
        c.drawCentredString(bx + box_w / 2, y + BOX_H - _hpx(35), ta)
        c.setFont("Noto", 5.6)
        c.drawCentredString(bx + box_w / 2, y + BOX_H - _hpx(51), en)

        c.setFont("Noto-Bold", 8.8)
        c.setFillColor(L.TEXT_COLOR)
        c.drawCentredString(bx + box_w / 2, y + _hpx(15), val)

        # Operator between boxes
        if i < 3:
            op_x = bx + box_w + OP_W / 2 - 5
            c.setFont("Noto-Bold", 9)
            c.setFillColor(L.TEXT_COLOR)
            c.drawString(op_x, y + BOX_H / 2 - 5, operators[i])

        bx += box_w + OP_W

    return y - 4


# ---------------------------------------------------------------------------
# Measurement pass — dry-run to find page-1 frame top
# ---------------------------------------------------------------------------
def _measure_frame_top(bill: Bill) -> float:
    dummy = rl_canvas.Canvas(io.BytesIO(), pagesize=A4)
    _draw_header(dummy)
    y = _draw_identity(dummy, bill, PAGE_H - HEADER_H)
    y = _draw_summary(dummy, bill, y)
    return y


# ---------------------------------------------------------------------------
# I + G + H — Payment slip, legal line, notice box — platypus Flowable
# ---------------------------------------------------------------------------
class _SlipFlowable(Flowable):
    """
    Last story item. Claims all remaining frame space (wrap returns availH).
    Forces a page break if space < _MIN_H.

    Local coordinate system when draw() is called:
        (0, 0) = page (LEFT=36, MARGIN=36)   ← bottom-left of slip
        y=_SLIP_H                             ← dashed tear-off line
        y=_SLIP_H + 4 + _NOTICE_H            ← notice box top
        y=_SLIP_H + 4 + _NOTICE_H + _LEGAL_H ← legal text top
    """
    _SLIP_H   = 126.0   # slip content below dashed line
    _NOTICE_H = 66.0    # notice box height
    _LEGAL_H  = 12.0    # legal text block
    _MIN_H    = _SLIP_H + 4 + _NOTICE_H + 4 + _LEGAL_H

    _LEGAL = (
        "*This electronic form of the bill has the same legal recognition, effect, validity or "
        "enforceability as the original form of the bill, in terms of the "
        "Electronic Transactions Act No.19 of 2006."
    )
    _NOTICE_EN = (
        "Please settle the arrears indicated in this invoice within 7 days to avoid "
        "possible disconnection of services as the due date has lapsed. "
        "If you have already settled the arrears please disregard this notice."
    )
    _NOTICE_SI = (
        "මෙම බිල්පතෙහි සඳහන් හිඟ මුදල දින 7ක් ඇතුළත ගෙවා සේවාව විසන්ධි වීම "
        "වළක්වා ගන්න."
    )
    _NOTICE_TA = (
        "இந்த பட்டியலில் குறிப்பிடப்பட்ட நிலுவைத் தொகையை 7 நாட்களுக்குள் செலுத்தி "
        "சேவை துண்டிப்பை தவிர்க்கவும்."
    )

    _LEGAL = (
        "*This electric form of the bill has the same legal recognition, effect, validity or "
        "enforceability as the original form of the bill, in terms of the "
        "Electronic Transactions Act No.19 of 2006."
    )
    _NOTICE_HEADING_SI = "දැනුම්දීම /"
    _NOTICE_HEADING_TA = "அறிவிப்பு /"
    _NOTICE_HEADING_EN = "Notice"
    _NOTICE_SI = (
        "මෙම බිල්පතේ සඳහන් මුදල ගෙවීමට ඇති බවත්, ගෙවිය යුතු මුදල ගෙවීමේ නියමිත දිනය "
        "ඉක්මවා ඇති බැවින් සේවා අත්හිටුවීම වළක්වා ගැනීම සඳහා දින 7ක් ඇතුළත මෙම "
        "බිල්පතේ සඳහන් බකී මුදල ගෙවන ලෙස කාරුණිකව දැනුම් දෙමු."
    )
    _NOTICE_TA = (
        "தயவுசெய்து இந்த விலைப்பட்டியலில் குறிப்பிடப்பட்டுள்ள நிலுவைத் தொகையை செலுத்த "
        "வேண்டிய இறுதி தேதியிலிருந்து 7 நாட்களுக்குள் செலுத்தவும். சேவைகள் "
        "துண்டிக்கப்படுவதைத் தவிர்க்க இதனைச் செய்யவும். நீங்கள் ஏற்கனவே நிலுவைத் "
        "தொகையைச் செலுத்தியிருந்தால், தயவுசெய்து இந்த அறிவிப்பை புறக்கணிக்கவும்."
    )
    _NOTICE_EN = (
        "Please settle the arrears indicated in this invoice within 7 days to avoid possible "
        "disconnection of services as the due date has lapsed. If you have already settled "
        "the arrears please disregard this notice."
    )

    def __init__(self, bill: Bill) -> None:
        super().__init__()
        self._bill = bill
        self._h    = self._MIN_H

    def wrap(self, availW: float, availH: float):
        if availH < self._MIN_H:
            return (availW, availH + 1)   # trigger page break
        self._h = availH
        # Claim 1 pt less than available so the slip never lands exactly on the
        # frame boundary — avoids floating-point precision failures at that edge.
        return (availW, availH - 1)

    # ------------------------------------------------------------------
    def draw(self) -> None:  # noqa: C901  (complex but self-contained)
        c  = self.canv
        b  = self._bill
        sh = self._SLIP_H   # local y of dashed line

        # ── G. Legal line ────────────────────────────────────────────────
        legal_base = sh + 4 + self._NOTICE_H + 4
        c.setFillColor(_LEGAL_BLUE)
        _fit_text(c, self._LEGAL, 0, legal_base + 4, CONTENT_W, "Noto", 5.7, 4.4)

        # ── H. Notice box ─────────────────────────────────────────────────
        nb_y = sh + 4                        # box bottom
        nb_h = self._NOTICE_H               # box height (54 pt)
        c.setFillColor(_NOTICE_FILL)
        c.setStrokeColor(_NOTICE_RED)
        c.setLineWidth(0.8)
        c.roundRect(0, nb_y, CONTENT_W, nb_h, 8, stroke=1, fill=1)

        # Heading  "ප්‍රකාශය / அறிவிப்பு / Notice"
        ht_y = nb_y + nb_h - 11
        c.setFont("NotoSinhala", 7.2)
        c.setFillColor(_NOTICE_RED)
        c.drawString(4, ht_y, "ප්‍රකාශය /")
        c.setFont("NotoTamil", 7.2)
        c.drawString(64, ht_y, "அறிவிப்பு /")
        c.setFont("Noto-Bold", 7.2)
        c.drawString(130, ht_y, "Notice")

        c.setFillColor(L.TEXT_COLOR)
        ly = ht_y - 9
        _fit_text(c, self._NOTICE_SI, 4, ly, CONTENT_W - 8, "NotoSinhala", 4.6, 3.8)
        ly -= 7.5
        _fit_text(c, self._NOTICE_TA, 4, ly, CONTENT_W - 8, "NotoTamil", 4.6, 3.8)
        ly -= 7.5
        first = (
            "Please settle the arrears indicated in this invoice within 7 days to avoid possible "
            "disconnection of services as the due date has lapsed. If you have already settled the arrears"
        )
        second = "please disregard this notice."
        _fit_text(c, first, 4, ly, CONTENT_W - 8, "Noto", 4.7, 3.8)
        ly -= 7.0
        _fit_text(c, second, 4, ly, CONTENT_W - 8, "Noto", 4.7, 3.8)

        # Redraw the notice with the exact current SLT wording and wrapped text.
        c.setFillColor(L.WHITE)
        c.rect(0, nb_y + 1, PAGE_W - LEFT, nb_h - 2, stroke=0, fill=1)
        c.setFillColor(_NOTICE_FILL)
        c.roundRect(0, nb_y, CONTENT_W, nb_h, 8, stroke=0, fill=1)
        c.setStrokeColor(_NOTICE_RED)
        c.setLineWidth(0.8)
        c.roundRect(0, nb_y, CONTENT_W, nb_h, 8, stroke=1, fill=0)

        def draw_para(text: str, font: str, size: float, leading: float,
                      x: float, top_y: float, width: float) -> float:
            def pieces(source: str) -> list[str]:
                out: list[str] = []
                for word in source.split():
                    if c.stringWidth(word, font, size) <= width:
                        out.append(word)
                        continue
                    chunk = ""
                    for ch in word:
                        candidate = chunk + ch
                        if chunk and c.stringWidth(candidate, font, size) > width:
                            out.append(chunk)
                            chunk = ch
                        else:
                            chunk = candidate
                    if chunk:
                        out.append(chunk)
                return out

            c.setFont(font, size)
            c.setFillColor(L.TEXT_COLOR)
            lines: list[str] = []
            current = ""
            for part in pieces(text):
                candidate = part if not current else f"{current} {part}"
                if current and c.stringWidth(candidate, font, size) > width:
                    lines.append(current)
                    current = part
                else:
                    current = candidate
            if current:
                lines.append(current)

            baseline = top_y - size
            for line in lines:
                c.drawString(x, baseline, line)
                baseline -= leading
            return baseline + size

        hx = 5.0
        ht_y = nb_y + nb_h - 12.0
        c.setFillColor(_NOTICE_RED)
        c.setFont("NotoSinhala", 8.0)
        c.drawString(hx, ht_y, self._NOTICE_HEADING_SI)
        hx += c.stringWidth(self._NOTICE_HEADING_SI, "NotoSinhala", 8.0) + 8
        c.setFont("NotoTamil", 8.0)
        c.drawString(hx, ht_y, self._NOTICE_HEADING_TA)
        hx += c.stringWidth(self._NOTICE_HEADING_TA, "NotoTamil", 8.0) + 8
        c.setFont("Noto-Bold", 8.0)
        c.drawString(hx, ht_y, self._NOTICE_HEADING_EN)

        text_top = ht_y - 7.0
        text_top = draw_para(self._NOTICE_SI, "NotoSinhala", 4.85, 5.7, 5, text_top, CONTENT_W - 10) - 1.0
        text_top = draw_para(self._NOTICE_TA, "NotoTamil", 4.75, 5.6, 5, text_top, CONTENT_W - 10) - 1.0
        draw_para(self._NOTICE_EN, "Noto", 4.85, 5.7, 5, text_top, CONTENT_W - 10)

        # ── Dashed tear-off separator (full page width) ─────────────────
        c.saveState()
        c.setDash(4, 3)
        c.setStrokeColor(L.MUTED_COLOR)
        c.setLineWidth(0.5)
        c.line(-LEFT, sh, PAGE_W - LEFT, sh)
        c.setDash()
        c.restoreState()

        # ── White background under the slip ─────────────────────────────
        c.setFillColor(L.WHITE)
        c.rect(-LEFT, 0, PAGE_W, sh, stroke=0, fill=1)

        # ── Slip layout constants ────────────────────────────────────────
        # Left panel : x=0   width=lw   (local coords, x=0 = page x=LEFT=36)
        # Right panel: x=rx  width=rw
        lw    = CONTENT_W * 0.50   # ≈ 261 pt
        rx    = lw + 10            # right panel start (local)
        rw    = CONTENT_W - rx

        FH    = 15.0   # field height
        FG    = 2.1    # gap between fields
        LBL_W = 86.0   # left-panel label box width
        RLW   = 82.0   # right-panel label box width

        # Helper: left-panel field (blue label | light value)
        def lfield(label: str, value: str, fy: float) -> None:
            c.setFillColor(_SLIP_LABEL)
            c.roundRect(0, fy, LBL_W, FH, 7, stroke=0, fill=1)
            c.setFont("Noto-Bold", 6.2)
            c.setFillColor(L.LABEL_BLUE)
            c.drawString(6, fy + 4, label)
            vw = lw - LBL_W
            c.setFillColor(L.WHITE)
            c.setStrokeColor(_SLIP_BORDER)
            c.setLineWidth(0.4)
            c.roundRect(LBL_W + 3, fy, vw - 3, FH, 7, stroke=1, fill=1)
            c.setFont("Noto", 7.8)
            c.setFillColor(L.TEXT_COLOR)
            _fit_text(c, value, LBL_W + 15, fy + 4, vw - 22, "Noto", 7.6, 5.0)

        # Helper: right-panel field (blue label | empty white box)
        def rfield(label: str, fy: float) -> None:
            c.setFillColor(_SLIP_LABEL)
            c.roundRect(rx, fy, RLW, FH, 7, stroke=0, fill=1)
            c.setFont("Noto-Bold", 6.2)
            c.setFillColor(L.LABEL_BLUE)
            c.drawString(rx + 6, fy + 4, label)
            vw = rw - RLW
            c.setFillColor(L.WHITE)
            c.setStrokeColor(_SLIP_BORDER)
            c.setLineWidth(0.4)
            c.roundRect(rx + RLW + 3, fy, vw - 3, FH, 7, stroke=1, fill=1)

        def date_boxes(start_x: float, fy: float) -> None:
            ex = start_x
            for group_digits, group_label in ((2, "DD"), (2, "MM"), (4, "YYYY")):
                c.setFont("Noto", 4.7)
                c.setFillColor(L.MUTED_COLOR)
                c.drawString(ex, fy + FH - 1, group_label)
                for _ in range(group_digits):
                    c.setStrokeColor(L.BOX_BORDER)
                    c.setFillColor(L.WHITE)
                    c.setLineWidth(0.4)
                    c.rect(ex, fy + 2, bsz, bsz, stroke=1, fill=1)
                    ex += bsz + 1
                ex += 4

        # ── Left panel: 6 fields top-down ───────────────────────────────
        fy = sh - 2 - FH  # first field top-right-of = sh-2; draw from fy
        lfield("Telephone No.",  b.telephone_number or "", fy)

        fy -= FG + FH
        lfield("Invoice No.",    b.invoice_number, fy)

        fy -= FG + FH
        lfield("Customer Name",  b.customer_name, fy)

        fy -= FG + FH
        lfield("Account No.",    b.account_number, fy)

        # Credit Card No. — 16 individual digit boxes (4 groups of 4)
        fy -= FG + FH
        c.setFillColor(_SLIP_LABEL)
        c.roundRect(0, fy, LBL_W, FH, 7, stroke=0, fill=1)
        c.setFont("Noto-Bold", 6.2)
        c.setFillColor(L.LABEL_BLUE)
        c.drawString(6, fy + 4, "Credit Card No.")
        # Draw 16 small input boxes
        bsz = 8.8   # box size
        bsp = 2.0   # space between groups
        cx  = LBL_W + 3
        for i in range(16):
            if i > 0 and i % 4 == 0:
                cx += bsp
            c.setStrokeColor(L.BOX_BORDER)
            c.setFillColor(L.WHITE)
            c.setLineWidth(0.4)
            c.rect(cx, fy + 2, bsz, bsz, stroke=1, fill=1)
            cx += bsz + 1

        # Card Expiry Date — DD / MM / YYYY boxes
        fy -= FG + FH
        c.setFillColor(_SLIP_LABEL)
        c.roundRect(0, fy, LBL_W, FH, 7, stroke=0, fill=1)
        c.setFont("Noto-Bold", 6.2)
        c.setFillColor(L.LABEL_BLUE)
        c.drawString(6, fy + 4, "Card Expiry Date")
        ex = LBL_W + 3
        # DD (2 boxes) / MM (2 boxes) / YYYY (4 boxes) with labels
        for group_digits, group_label in ((2, "DD"), (2, "MM"), (4, "YYYY")):
            c.setFont("Noto", 4.7)
            c.setFillColor(L.MUTED_COLOR)
            c.drawString(ex, fy + FH - 1, group_label)
            for _ in range(group_digits):
                c.setStrokeColor(L.BOX_BORDER)
                c.setFillColor(L.WHITE)
                c.setLineWidth(0.4)
                c.rect(ex, fy + 2, bsz, bsz, stroke=1, fill=1)
                ex += bsz + 1
            ex += 4  # gap between groups

        # ── Right panel: "Payment Slip" tag + barcode ───────────────────
        # Top strip: teal "Payment Slip" label
        tag_y  = sh - 2 - FH     # same top as left field row 1
        tag_w  = 73.0
        c.setFillColor(L.HEADER_BLUE)
        c.roundRect(rx, tag_y, tag_w, FH, 7, stroke=0, fill=1)
        c.setFont("Noto-Bold", 8.0)
        c.setFillColor(L.WHITE)
        c.drawString(rx + 4, tag_y + 4, "Payment Slip")

        qr_sz = 33.0
        qr_bx = rx + rw - qr_sz
        qr_by = tag_y - 18
        logo_w = 42.0
        logo_h = 14.0
        logo_x = qr_bx - logo_w - 4

        bc_x = rx + tag_w + 5
        bc_y = tag_y + 1.5
        bc_w = max(72.0, logo_x - bc_x - 4)
        draw_barcode(c, b.invoice_number, bc_x, bc_y, w=bc_w, h=13)

        try:
            c.drawImage(
                L.LOGO_PATH,
                logo_x, tag_y - 1,
                width=logo_w, height=logo_h,
                preserveAspectRatio=True, anchor="c", mask="auto",
            )
        except Exception:
            pass

        c.setFont("Noto", 4.8)
        c.setFillColor(L.MUTED_COLOR)
        c.drawCentredString(logo_x + logo_w / 2, tag_y - 8, "LANKAQR")

        # ── Right-panel fields (below barcode) ──────────────────────────
        draw_qr(
            c,
            f"https://www.slt.lk/payonline?inv={b.invoice_number}",
            qr_bx, qr_by, size=qr_sz,
        )

        ry = tag_y - 22

        # Checkboxes: Cash / Cheques / Credit Card
        c.setFillColor(L.WHITE)
        c.rect(rx, ry, rw, FH, stroke=0, fill=1)
        cbx = rx + 4
        for label in ("Cash", "Cheques", "Credit Card"):
            c.setStrokeColor(_SLIP_BORDER)
            c.setFillColor(L.WHITE)
            c.setLineWidth(0.5)
            c.rect(cbx, ry + 3, 8.5, 8.5, stroke=1, fill=0)
            c.setFont("Noto-Bold", 6.4)
            c.setFillColor(L.LABEL_BLUE)
            c.drawString(cbx + 11, ry + 4, label)
            cbx += 58

        ry -= FG
        rfield("Name of Bank",          ry - FH);  ry -= FH + FG
        rfield("Cheque Number",         ry - FH);  ry -= FH + FG
        rfield("Amount",                ry - FH);  ry -= FH + FG
        rfield("Customer's Signature",  ry - FH);  ry -= FH + FG
        date_y = ry - FH
        c.setFillColor(_SLIP_LABEL)
        c.roundRect(rx, date_y, RLW, FH, 7, stroke=0, fill=1)
        c.setFont("Noto-Bold", 6.2)
        c.setFillColor(L.LABEL_BLUE)
        c.drawString(rx + 6, date_y + 4, "Date")
        date_boxes(rx + RLW + 3, date_y)
        c.setFont("Noto", 5.4)
        c.setFillColor(L.TEXT_COLOR)
        c.drawRightString(rx + rw - 2, date_y + 4, "1B56510565")

# ---------------------------------------------------------------------------
# Platypus story — D (charges) + E (payments) + I/G/H (slip)
# ---------------------------------------------------------------------------
_DESC_W = CONTENT_W - 90.0
_AMT_W  = 90.0
_DATE_W = 78.0

def _para_styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle("base", fontName="Noto", fontSize=7.2,
                          leading=9.2, textColor=L.TEXT_COLOR,
                          spaceAfter=0, spaceBefore=0)
    return {
        "base":  base,
        "bold":  ParagraphStyle("bold",  parent=base, fontName="Noto-Bold"),
        "hdg":   ParagraphStyle("hdg",   parent=base, fontName="Noto-Bold", fontSize=7.4),
        "section": ParagraphStyle("section", parent=base, fontName="Noto-Bold", fontSize=11.5, leading=13),
        "muted": ParagraphStyle("muted", parent=base, textColor=L.MUTED_COLOR),
        "right": ParagraphStyle("right", parent=base, alignment=TA_RIGHT),
        "rbold": ParagraphStyle("rbold", parent=base, fontName="Noto-Bold", alignment=TA_RIGHT),
    }

_BASE_TS = [
    ("FONTNAME",      (0, 0), (-1, -1), "Noto"),
    ("FONTSIZE",      (0, 0), (-1, -1), 7.2),
    ("TEXTCOLOR",     (0, 0), (-1, -1), L.TEXT_COLOR),
    ("TOPPADDING",    (0, 0), (-1, -1), 1),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ("LEFTPADDING",   (0, 0), (-1, -1), 0),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
]


class _ChargesHeadingFlowable(Flowable):
    """Draw the charges heading with the SLT-style rule and amount label."""

    _H = 19.0
    _TITLE = "DETAILS OF CHARGES FOR THE PERIOD"

    def wrap(self, availW: float, availH: float):
        return (availW, self._H)

    def draw(self) -> None:
        c = self.canv
        title_size = 11.5
        title_y = 6.5

        c.setFont("Noto-Bold", title_size)
        c.setFillColor(L.LABEL_BLUE)
        c.drawString(0, title_y, self._TITLE)

        rule_x = c.stringWidth(self._TITLE, "Noto-Bold", title_size) + 6
        c.setStrokeColor(L.LABEL_BLUE)
        c.setLineWidth(0.6)
        c.line(rule_x, title_y + 3.0, CONTENT_W, title_y + 3.0)

        c.setFont("Noto-Bold", 6.7)
        c.setFillColor(L.TEXT_COLOR)
        c.drawRightString(CONTENT_W - 4, 0, "(Rs.)")


def _build_story(bill: Bill) -> list:
    st = _para_styles()
    story: list = []

    # ── D. Details of Charges ─────────────────────────────────────────────
    story.append(_ChargesHeadingFlowable())

    # Charge rows (grouped by service account)
    data: list[list] = []
    cmds: list       = list(_BASE_TS)
    ri = 0

    for grp in bill.groups:
        data.append([Paragraph(grp.service_number, st["bold"]), ""])
        cmds += [("TOPPADDING",    (0, ri), (-1, ri), 3),
                 ("BOTTOMPADDING", (0, ri), (-1, ri), 2)]
        ri += 1

        for li in grp.lines:
            period = _period_str(li.period_start, li.period_end)
            label  = f"    {li.description}"
            if period:
                label += f"  [{period}]"
            data.append([Paragraph(label, st["base"]),
                         Paragraph(_fmt_amount(li.amount), st["right"])])
            ri += 1

        data.append(["", ""])
        cmds += [("TOPPADDING",    (0, ri), (-1, ri), 0),
                 ("BOTTOMPADDING", (0, ri), (-1, ri), 3)]
        ri += 1

    if bill.tax_lines:
        data.append([Paragraph("Taxes &amp; Levies", st["bold"]), ""])
        cmds.append(("TOPPADDING", (0, ri), (-1, ri), 3))
        ri += 1
        for li in bill.tax_lines:
            data.append([Paragraph(f"    {li.description}", st["base"]),
                         Paragraph(_fmt_amount(li.amount), st["right"])])
            ri += 1

    # Gap row + totals
    data.append(["", ""])
    cmds += [("TOPPADDING",    (0, ri), (-1, ri), 0),
             ("BOTTOMPADDING", (0, ri), (-1, ri), 0)]
    ri += 1

    data.append([Paragraph("Total Charges for the Period", st["bold"]),
                 Paragraph(_fmt_amount(bill.summary.charges_for_period), st["rbold"])])
    cmds += [("LINEABOVE",     (0, ri), (-1, ri), 0.6, L.TEXT_COLOR),
             ("LINEBELOW",     (0, ri), (-1, ri), 0.6, L.TEXT_COLOR),
             ("TOPPADDING",    (0, ri), (-1, ri), 4),
             ("BOTTOMPADDING", (0, ri), (-1, ri), 4)]

    if data:
        charge_table = Table(data, colWidths=[_DESC_W, _AMT_W], splitByRow=True)
        charge_table.setStyle(TableStyle(cmds))
        story.append(charge_table)

    story.append(Spacer(0, 6))

    # ── E. Details of Payments ────────────────────────────────────────────
    pdata: list[list] = []
    pcmds: list = [
        ("FONTNAME",      (0, 0), (-1, -1), "Noto"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.2),
        ("TEXTCOLOR",     (0, 0), (-1, -1), L.TEXT_COLOR),
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (2, 0), (2, -1), 8),
        ("ALIGN",         (2, 0), (2, -1), "RIGHT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]
    pdata.append([Paragraph("Details of Payments Received", st["hdg"]), "", ""])
    pcmds += [("SPAN", (0, 0), (2, 0)), ("BOTTOMPADDING", (0, 0), (-1, 0), 4)]
    pri = 1

    if bill.payments:
        for pmt in bill.payments:
            label = pmt.reference or pmt.method
            pdata.append([
                Paragraph(f"  {label}", st["base"]),
                Paragraph(_fmt_date(pmt.payment_date), st["base"]),
                _fmt_amount(pmt.amount),
            ])
            pri += 1
    else:
        pdata.append([Paragraph("  No payments received this period", st["muted"]), "", ""])
        pcmds.append(("SPAN", (0, pri), (2, pri)))
        pri += 1

    pdata.append([Paragraph("Total Payments Received", st["bold"]),
                  "",
                  _fmt_amount(bill.summary.payments_received)])
    pcmds += [("FONTNAME",   (0, pri), (0, pri), "Noto-Bold"),
              ("FONTNAME",   (2, pri), (2, pri), "Noto-Bold"),
              ("TOPPADDING", (0, pri), (-1, pri), 3),
              ("BOTTOMPADDING", (0, pri), (-1, pri), 1)]

    left_block_w = CONTENT_W * 0.49
    right_block_w = CONTENT_W - left_block_w - 10
    date_w = 58.0
    amount_w = 58.0
    dw = left_block_w - date_w - amount_w
    pmt_table = Table(
        pdata,
        colWidths=[dw, date_w, amount_w],
        rowHeights=[12] + [11.5] * (len(pdata) - 1),
        splitByRow=True,
    )
    pmt_table.setStyle(TableStyle(pcmds))

    usage_title = (
        "Detailed Usage Charges for Additional Channels "
        f"{bill.telephone_number or ''}"
    )
    udata: list[list] = [
        [Paragraph(usage_title, st["hdg"]), "", "", ""],
        [Paragraph("Date &amp; Time", st["bold"]),
         Paragraph("Service Type", st["bold"]),
         Paragraph("Description", st["bold"]),
         Paragraph("Charge", st["bold"])],
    ]
    for u in bill.usage_records:
        udata.append([
            Paragraph(_fmt_datetime(u.event_time), st["base"]),
            Paragraph(u.service_type, st["base"]),
            Paragraph(u.description, st["base"]),
            Paragraph(_fmt_amount(u.charge), st["right"]),
        ])

    ucmds: list = [
        ("FONTNAME",      (0, 0), (-1, -1), "Noto"),
        ("FONTSIZE",      (0, 0), (-1, -1), 6.4),
        ("TEXTCOLOR",     (0, 0), (-1, -1), L.TEXT_COLOR),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("SPAN",          (0, 0), (-1, 0)),
        ("FONTNAME",      (0, 0), (0, 0), "Noto-Bold"),
        ("LINEABOVE",     (0, 1), (-1, 1), 0.7, L.TEXT_COLOR),
        ("LINEBELOW",     (0, 1), (-1, 1), 0.7, L.TEXT_COLOR),
        ("BOX",           (0, 1), (-1, -1), 0.5, L.TEXT_COLOR),
        ("ALIGN",         (3, 1), (3, -1), "RIGHT"),
    ]
    usage_table = Table(
        udata,
        colWidths=[right_block_w * 0.24, right_block_w * 0.23, right_block_w * 0.34, right_block_w * 0.19],
        rowHeights=[10, 10] + [8] * max(0, len(udata) - 2),
        splitByRow=True,
    )
    usage_table.setStyle(TableStyle(ucmds))

    lower = Table([[pmt_table, usage_table]], colWidths=[left_block_w, right_block_w])
    lower.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("LINEBEFORE",   (1, 0), (1, 0), 0.8, L.TEXT_COLOR),
        ("LEFTPADDING",  (1, 0), (1, 0), 10),
    ]))
    story.append(lower)

    # ── I/G/H — Payment slip (anchored to bottom of last page) ───────────
    story.append(_SlipFlowable(bill))

    return story


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def render_bill(bill: Bill, out_path: str | None = None) -> str:
    """Render a Bill to PDF. Returns the output path."""
    if out_path is None:
        out_dir = Path("output")
        out_dir.mkdir(exist_ok=True)
        safe = bill.account_number.replace(" ", "-")
        out_path = str(out_dir / f"{safe}_{bill.period_start}_{bill.period_end}.pdf")

    frame_top = _measure_frame_top(bill)

    # Page-1 frame: from below C (summary) to bottom margin.
    # Slip/legal/notice are all in _SlipFlowable — no reservation needed.
    p1_frame = Frame(
        LEFT, MARGIN,
        CONTENT_W, max(frame_top - MARGIN, 1),
        leftPadding=0, rightPadding=0, topPadding=4, bottomPadding=0,
        showBoundary=0,
    )

    # Continuation-page frame: from below slim header to bottom margin.
    later_h = PAGE_H - SLIM_H - 6 - MARGIN
    later_frame = Frame(
        LEFT, MARGIN,
        CONTENT_W, later_h,
        leftPadding=0, rightPadding=0, topPadding=6, bottomPadding=0,
        showBoundary=0,
    )

    def on_first(c: rl_canvas.Canvas, doc: BaseDocTemplate) -> None:
        _draw_header(c)
        y = _draw_identity(c, bill, PAGE_H - HEADER_H)
        _draw_summary(c, bill, y)

    def on_later(c: rl_canvas.Canvas, doc: BaseDocTemplate) -> None:
        _draw_slim_header(c)

    p1_tpl    = PageTemplate(id="first", frames=[p1_frame],    onPage=on_first)
    later_tpl = PageTemplate(id="later", frames=[later_frame], onPage=on_later)

    doc = BaseDocTemplate(out_path, pagesize=A4,
                          leftMargin=0, rightMargin=0,
                          topMargin=0, bottomMargin=0)
    doc.addPageTemplates([p1_tpl, later_tpl])

    story = [NextPageTemplate("later")] + _build_story(bill)
    doc.build(story, canvasmaker=_NumberedCanvas)
    return out_path


if __name__ == "__main__":
    from datetime import date as _date
    from app.billing.engine import build_bill
    from app.db.base import SessionLocal

    _session = SessionLocal()
    try:
        _bill = build_bill(_session, "004 152 4075", _date(2024, 1, 24), _date(2024, 2, 23))
    finally:
        _session.close()

    print(f"PDF written: {render_bill(_bill)}")
