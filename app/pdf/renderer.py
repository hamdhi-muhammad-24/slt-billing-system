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
    HRFlowable,
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

HEADER_H = 70.0
SLIM_H   = 30.0

# Extra colours used only in the renderer
_ORANGE_FILL   = HexColor("#FFF8E1")
_ORANGE_BORDER = HexColor("#FFA000")
_PURPLE_FILL   = HexColor("#6A1B9A")
_NOTICE_FILL   = HexColor("#FFF5F5")
_NOTICE_RED    = HexColor("#CC0000")


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
    c.setFont("Noto-Bold", 24)
    c.setFillColor(L.WHITE)
    c.drawString(LEFT, y + 32, "INVOICE")

    c.setFont("Noto-Bold", 7.5)
    c.drawString(LEFT + 108, y + 42, "Sri Lanka Telecom PLC")
    c.setFont("Noto", 7)
    c.drawString(LEFT + 108, y + 32, "Lotus Road, P.O Box 503, Colombo 01.")

    # SLT MOBITEL logo — right side, preserving aspect ratio, no background
    logo_h = HEADER_H - 10.0
    logo_w = 130.0
    try:
        c.drawImage(
            L.LOGO_PATH,
            RIGHT - logo_w, y + (HEADER_H - logo_h) / 2,
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

    left_w   = CONTENT_W * 0.44          # ≈ 230 pt
    right_x  = LEFT + left_w + 10        # ≈ 276 pt (page coords)
    right_w  = CONTENT_W - left_w - 10   # ≈ 283 pt

    # Split right column into inner content column + narrow QR/app column
    _QR_W   = 68.0
    inner_w = right_w - _QR_W - 5        # ≈ 210 pt
    qr_x    = right_x + inner_w + 5      # ≈ 491 pt (page coords)

    y = top_y - 10  # left-column cursor

    # ── Left column ──────────────────────────────────────────────────────
    c.setFont("Noto", 6.5)
    c.setFillColor(L.LABEL_BLUE)
    c.drawString(LEFT, y, "TELEPHONE NUMBER")
    c.setFont("Noto-Bold", 9.5)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT + 108, y, bill.telephone_number or "")
    y -= 5

    ROW_H = 15.0
    ROW_G = 4.0

    def left_field(label: str, value: str) -> None:
        nonlocal y
        y -= ROW_H + ROW_G
        L.draw_field_box(c, label, value, LEFT, y, left_w, h=ROW_H)

    left_field("Account Number", bill.account_number)
    left_field("Invoice Number",  bill.invoice_number)
    left_field("Billing Date",    _fmt_date(bill.billing_date))
    left_field("Billing Period",  _period_str(bill.period_start, bill.period_end))
    bottom_left = y   # bottom of left column

    # ── Inner right column ────────────────────────────────────────────────
    ry = top_y - 10   # inner-column cursor (page y, counts down)

    # Customer address box (green border)
    cust_h = 52.0
    ry -= cust_h
    c.setStrokeColor(L.GREEN_BORDER)
    c.setLineWidth(1.0)
    c.setFillColor(L.LIGHT_GREY)
    c.rect(right_x, ry, inner_w, cust_h, stroke=1, fill=1)

    c.setFont("Noto", 6.5)
    c.setFillColor(L.MUTED_COLOR)
    c.drawString(right_x + 5, ry + cust_h - 10, "Rev. Mr / Mrs.")
    c.setFont("Noto-Bold", 9)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(right_x + 5, ry + cust_h - 21, bill.customer_name)
    c.setFont("Noto", 8)
    addr_y = ry + cust_h - 33
    for line in bill.address_lines:
        c.drawString(right_x + 5, addr_y, line)
        addr_y -= 10

    # Barcode (invoice number) under customer box
    ry -= 3
    bc_h = 20.0
    ry -= bc_h
    draw_barcode(c, bill.invoice_number, right_x, ry, w=inner_w, h=bc_h)

    # Service-label banner
    ry -= 3
    banner_h = 13.0
    ry -= banner_h
    c.setFillColor(L.TEAL_FILL)
    c.rect(right_x, ry, inner_w, banner_h, stroke=0, fill=1)
    c.setFont("Noto-Bold", 7.5)
    c.setFillColor(L.WHITE)
    c.drawString(right_x + 6, ry + 3, (bill.service_label or "").upper())

    # Reference line (invoice ref + service tag) — small muted text
    ry -= 3
    ref = f"{bill.invoice_number}  {bill.service_label or 'LTE service'}"
    c.setFont("Noto", 5.5)
    c.setFillColor(L.MUTED_COLOR)
    c.drawString(right_x, ry, ref)
    ry -= 8

    # "www.slt.lk/payonline" link
    c.setFont("Noto", 5.5)
    c.setFillColor(L.LABEL_BLUE)
    c.drawString(right_x, ry, "www.slt.lk/payonline")
    inner_bottom = ry - 4   # lowest point of inner column

    # ── QR / MySLT column ─────────────────────────────────────────────────
    # "X of N" is painted by _NumberedCanvas at page y ≈ top_y - 10;
    # start the QR box 14 pt below that to leave it clear.
    qry = top_y - 10 - 14

    # QR code in amber rounded box
    qr_box = _QR_W - 4          # ≈ 64 pt square
    qry -= qr_box
    c.setFillColor(_ORANGE_FILL)
    c.setStrokeColor(_ORANGE_BORDER)
    c.setLineWidth(1.0)
    c.roundRect(qr_x, qry, _QR_W, qr_box, 4, stroke=1, fill=1)
    draw_qr(
        c,
        f"https://www.slt.lk/payonline?inv={bill.invoice_number}",
        qr_x + 4, qry + 4, size=qr_box - 8,
    )

    # MySLT app icon in purple rounded box
    qry -= 4
    app_h = 40.0
    qry -= app_h
    c.setFillColor(_PURPLE_FILL)
    c.roundRect(qr_x, qry, _QR_W, app_h, 4, stroke=0, fill=1)
    c.setFont("Noto-Bold", 9)
    c.setFillColor(L.WHITE)
    c.drawCentredString(qr_x + _QR_W / 2, qry + app_h / 2 - 2, "MySLT")
    c.setFont("Noto", 5.5)
    c.drawCentredString(qr_x + _QR_W / 2, qry + app_h / 2 - 12, "The App")

    # Small "www" label under MySLT box
    qry -= 3
    c.setFont("Noto", 5)
    c.setFillColor(L.LABEL_BLUE)
    c.drawCentredString(qr_x + _QR_W / 2, qry - 6,  "www.slt.lk/")
    c.drawCentredString(qr_x + _QR_W / 2, qry - 14, "payonline")
    qr_bottom = qry - 16

    return min(bottom_left, inner_bottom, qr_bottom) - 8


# ---------------------------------------------------------------------------
# C. Summary of Invoice
# ---------------------------------------------------------------------------
def _draw_summary(c: rl_canvas.Canvas, bill: Bill, top_y: float) -> float:
    """Draw 5-box summary row; return y below it."""
    y = top_y - 4
    # Section heading + rule
    c.setFont("Noto-Bold", 8.5)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT, y, "SUMMARY OF INVOICE")
    y -= 3
    L.hrule(c, LEFT, y, CONTENT_W, color=L.BOX_BORDER, lw=0.6)
    y -= 4

    BOX_H = 54.0
    OP_W  = 13.0
    box_w = (CONTENT_W - 4 * OP_W) / 5.0

    boxes = [
        ("ශේෂ ගෙනෙන",         "Balance B/F",            _fmt_amount(bill.summary.balance_bf),         False),
        ("ලැබුණු ගෙවීම්",      "Payments received",      _fmt_amount(bill.summary.payments_received),  False),
        ("කාල සීමාවේ ගාස්තු", "Charges for the period", _fmt_amount(bill.summary.charges_for_period), False),
        ("ගෙවිය යුතු මුළු",    "Total payable",          _fmt_amount(bill.summary.total_payable),      True),
        ("ගෙවීමේ දිනය",        "Payment due date",       _fmt_date(bill.due_date),                     True),
    ]
    operators = ["−", "+", "="]

    y -= BOX_H
    bx = LEFT
    for i, (si, en, val, teal) in enumerate(boxes):
        fill_c  = L.TEAL_FILL if teal else L.WHITE
        lbl_c   = L.WHITE     if teal else L.LABEL_BLUE
        muted_c = L.WHITE     if teal else L.MUTED_COLOR
        val_c   = L.WHITE     if teal else L.TEXT_COLOR

        c.setFillColor(fill_c)
        c.setStrokeColor(L.TEAL_BORDER)
        c.setLineWidth(0.8)
        c.roundRect(bx, y, box_w, BOX_H, 4, stroke=1, fill=1)

        # Sinhala caption
        c.setFont("NotoSinhala", 5.5)
        c.setFillColor(lbl_c)
        c.drawString(bx + 4, y + BOX_H - 12, si)

        # English caption
        c.setFont("Noto", 5.5)
        c.setFillColor(muted_c)
        c.drawString(bx + 4, y + BOX_H - 22, en)

        # Value
        c.setFont("Noto-Bold", 10)
        c.setFillColor(val_c)
        c.drawString(bx + 4, y + 8, val)

        # Operator between boxes
        if i < 3:
            op_x = bx + box_w + OP_W / 2 - 5
            c.setFont("Noto-Bold", 9)
            c.setFillColor(L.TEXT_COLOR)
            c.drawString(op_x, y + BOX_H / 2 - 5, operators[i])

        bx += box_w + OP_W

    return y - 10


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
    _SLIP_H   = 168.0   # slip content below dashed line
    _NOTICE_H = 50.0    # notice box height
    _LEGAL_H  = 24.0    # two-line legal text block
    _MIN_H    = _SLIP_H + 4 + _NOTICE_H + 4 + _LEGAL_H  # = 250 pt

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
        mid  = len(self._LEGAL) // 2
        cut  = self._LEGAL.rfind(" ", 0, mid)
        c.setFont("Noto", 5.5)
        c.setFillColor(L.MUTED_COLOR)
        c.drawString(0, legal_base + 10, self._LEGAL[:cut])
        c.drawString(0, legal_base,      self._LEGAL[cut + 1:])

        # ── H. Notice box ─────────────────────────────────────────────────
        nb_y = sh + 4                        # box bottom
        nb_h = self._NOTICE_H               # box height (54 pt)
        c.setFillColor(_NOTICE_FILL)
        c.setStrokeColor(_NOTICE_RED)
        c.setLineWidth(0.8)
        c.rect(0, nb_y, CONTENT_W, nb_h, stroke=1, fill=1)

        # Heading  "ප්‍රකාශය / அறிவிப்பு / Notice"
        ht_y = nb_y + nb_h - 12
        c.setFont("NotoSinhala", 7)
        c.setFillColor(_NOTICE_RED)
        c.drawString(4, ht_y, "ප්‍රකාශය /")
        c.setFont("NotoTamil", 7)
        c.drawString(64, ht_y, "அறிவிப்பு /")
        c.setFont("Noto-Bold", 7)
        c.drawString(130, ht_y, "Notice")

        # English body text (wrap into ~3 lines)
        body = self._NOTICE_EN
        cut1 = body.rfind(" ", 0, len(body) // 3)
        cut2 = body.rfind(" ", 0, 2 * len(body) // 3)
        lines = [body[:cut1], body[cut1 + 1:cut2], body[cut2 + 1:]]
        c.setFont("Noto", 5.5)
        c.setFillColor(L.TEXT_COLOR)
        ly = ht_y - 11
        for line in lines:
            c.drawString(4, ly, line)
            ly -= 9

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
        rw    = CONTENT_W - lw - 10

        FH    = 13.0   # field height
        FG    = 2.0    # gap between fields
        LBL_W = 82.0   # left-panel label box width
        RLW   = 80.0   # right-panel label box width

        # Helper: left-panel field (blue label | light value)
        def lfield(label: str, value: str, fy: float) -> None:
            c.setFillColor(L.HEADER_BLUE)
            c.rect(0, fy, LBL_W, FH, stroke=0, fill=1)
            c.setFont("Noto", 5.5)
            c.setFillColor(L.WHITE)
            c.drawString(2, fy + 3, label)
            vw = lw - LBL_W
            c.setFillColor(L.LIGHT_GREY)
            c.setStrokeColor(L.BOX_BORDER)
            c.setLineWidth(0.4)
            c.rect(LBL_W, fy, vw, FH, stroke=1, fill=1)
            c.setFont("Noto", 7.5)
            c.setFillColor(L.TEXT_COLOR)
            c.drawString(LBL_W + 3, fy + 3, value)

        # Helper: right-panel field (blue label | empty white box)
        def rfield(label: str, fy: float) -> None:
            c.setFillColor(L.HEADER_BLUE)
            c.rect(rx, fy, RLW, FH, stroke=0, fill=1)
            c.setFont("Noto", 5.5)
            c.setFillColor(L.WHITE)
            c.drawString(rx + 2, fy + 3, label)
            vw = rw - RLW
            c.setFillColor(L.WHITE)
            c.setStrokeColor(L.BOX_BORDER)
            c.setLineWidth(0.4)
            c.rect(rx + RLW, fy, vw, FH, stroke=1, fill=1)

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
        c.setFillColor(L.HEADER_BLUE)
        c.rect(0, fy, LBL_W, FH, stroke=0, fill=1)
        c.setFont("Noto", 5.5)
        c.setFillColor(L.WHITE)
        c.drawString(2, fy + 3, "Credit Card No.")
        # Draw 16 small input boxes
        bsz = 8.0   # box size
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
        c.setFillColor(L.HEADER_BLUE)
        c.rect(0, fy, LBL_W, FH, stroke=0, fill=1)
        c.setFont("Noto", 5.5)
        c.setFillColor(L.WHITE)
        c.drawString(2, fy + 3, "Card Expiry Date")
        ex = LBL_W + 3
        # DD (2 boxes) / MM (2 boxes) / YYYY (4 boxes) with labels
        for group_digits, group_label in ((2, "DD"), (2, "MM"), (4, "YYYY")):
            c.setFont("Noto", 4.5)
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
        tag_w  = rw * 0.45
        c.setFillColor(L.HEADER_BLUE)
        c.rect(rx, tag_y, tag_w, FH, stroke=0, fill=1)
        c.setFont("Noto-Bold", 7.5)
        c.setFillColor(L.WHITE)
        c.drawString(rx + 3, tag_y + 3, "Payment Slip")

        # SLT logo in the tag header (right of "Payment Slip")
        try:
            c.drawImage(
                L.LOGO_PATH,
                rx + tag_w + 3, tag_y,
                width=rw - tag_w - 3, height=FH,
                preserveAspectRatio=True, anchor="c", mask="auto",
            )
        except Exception:
            pass

        # Barcode below tag, spanning full right-panel width
        bc_y = tag_y - FG - 22
        draw_barcode(c, b.invoice_number, rx, bc_y, w=rw, h=22)

        # ── Right-panel fields (below barcode) ──────────────────────────
        ry = bc_y - FG   # cursor for right-panel fields

        # Checkboxes: Cash / Cheques / Credit Card
        ry -= FH
        c.setFillColor(L.HEADER_BLUE)
        c.rect(rx, ry, rw, FH, stroke=0, fill=1)
        cbx = rx + 4
        for label in ("Cash", "Cheques", "Credit Card"):
            c.setStrokeColor(L.WHITE)
            c.setFillColor(L.WHITE)
            c.setLineWidth(0.5)
            c.rect(cbx, ry + 2, 8, 8, stroke=1, fill=0)
            c.setFont("Noto", 6)
            c.setFillColor(L.WHITE)
            c.drawString(cbx + 10, ry + 3, label)
            cbx += 56

        ry -= FG
        rfield("Name of Bank",          ry - FH);  ry -= FH + FG
        rfield("Cheque Number",         ry - FH);  ry -= FH + FG
        rfield("Amount",                ry - FH);  ry -= FH + FG
        rfield("Customer's Signature",  ry - FH);  ry -= FH + FG
        rfield("Date",                  ry - FH);  ry -= FH + FG

        # ── Bottom section: SLT logo (left) + QR + LANKAQR label ────────
        bottom_h = max(ry, 4)           # available height above y=0
        # Leave 8pt below the QR start for the LANKAQR label (7pt) + 1pt gap
        qr_sz = min(30.0, max(bottom_h - 8, 8))
        qr_by = bottom_h - qr_sz       # QR bottom y
        qr_bx = rx + rw - qr_sz        # QR x (right-aligned)

        draw_qr(
            c,
            f"https://www.slt.lk/payonline?inv={b.invoice_number}",
            qr_bx, qr_by, size=qr_sz,
        )

        # LANKAQR label sits below the QR code
        c.setFont("Noto", 5)
        c.setFillColor(L.MUTED_COLOR)
        c.drawCentredString(qr_bx + qr_sz / 2, max(1, qr_by - 7), "LANKAQR")

        # SLT Mobitel logo — left portion of bottom section, centred on QR height
        logo_h = min(16.0, qr_sz)
        logo_w = min(qr_bx - rx - 4, rw * 0.42)
        try:
            c.drawImage(
                L.LOGO_PATH,
                rx, qr_by + (qr_sz - logo_h) / 2,
                width=logo_w, height=logo_h,
                preserveAspectRatio=True, anchor="w", mask="auto",
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Platypus story — D (charges) + E (payments) + I/G/H (slip)
# ---------------------------------------------------------------------------
_DESC_W = CONTENT_W - 90.0
_AMT_W  = 90.0
_DATE_W = 78.0

def _para_styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle("base", fontName="Noto", fontSize=8,
                          leading=11, textColor=L.TEXT_COLOR,
                          spaceAfter=0, spaceBefore=0)
    return {
        "base":  base,
        "bold":  ParagraphStyle("bold",  parent=base, fontName="Noto-Bold"),
        "hdg":   ParagraphStyle("hdg",   parent=base, fontName="Noto-Bold", fontSize=8.5),
        "muted": ParagraphStyle("muted", parent=base, textColor=L.MUTED_COLOR),
        "right": ParagraphStyle("right", parent=base, alignment=TA_RIGHT),
        "rbold": ParagraphStyle("rbold", parent=base, fontName="Noto-Bold", alignment=TA_RIGHT),
    }

_BASE_TS = [
    ("FONTNAME",      (0, 0), (-1, -1), "Noto"),
    ("FONTSIZE",      (0, 0), (-1, -1), 8),
    ("TEXTCOLOR",     (0, 0), (-1, -1), L.TEXT_COLOR),
    ("TOPPADDING",    (0, 0), (-1, -1), 1),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ("LEFTPADDING",   (0, 0), (-1, -1), 0),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
]


def _build_story(bill: Bill) -> list:
    st = _para_styles()
    story: list = []

    # ── D. Details of Charges ─────────────────────────────────────────────
    story.append(HRFlowable(width="100%", color=L.BOX_BORDER, thickness=0.5,
                             spaceAfter=3))

    title_row = Table(
        [[Paragraph("DETAILS OF CHARGES FOR THE PERIOD", st["hdg"]),
          Paragraph("(Rs.)", st["muted"])]],
        colWidths=[_DESC_W, _AMT_W],
    )
    title_row.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ALIGN",         (1, 0), (1, 0),  "RIGHT"),
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
    ]))
    story.append(title_row)

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
    cmds += [("LINEABOVE",     (0, ri), (-1, ri), 0.5, L.BOX_BORDER),
             ("TOPPADDING",    (0, ri), (-1, ri), 4),
             ("BOTTOMPADDING", (0, ri), (-1, ri), 2)]

    if data:
        charge_table = Table(data, colWidths=[_DESC_W, _AMT_W], splitByRow=True)
        charge_table.setStyle(TableStyle(cmds))
        story.append(charge_table)

    story.append(Spacer(0, 6))

    # ── E. Details of Payments ────────────────────────────────────────────
    pdata: list[list] = []
    pcmds: list = [
        ("FONTNAME",      (0, 0), (-1, -1), "Noto"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("TEXTCOLOR",     (0, 0), (-1, -1), L.TEXT_COLOR),
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("ALIGN",         (2, 0), (2, -1), "RIGHT"),
    ]
    pdata.append([Paragraph("Details of Payments Received", st["hdg"]), "", ""])
    pcmds += [("SPAN", (0, 0), (2, 0)), ("BOTTOMPADDING", (0, 0), (-1, 0), 3)]
    pri = 1

    if bill.payments:
        for pmt in bill.payments:
            label = pmt.reference or pmt.method
            pdata.append([
                Paragraph(f"  {label}", st["base"]),
                Paragraph(_fmt_date(pmt.payment_date), st["base"]),
                Paragraph(_fmt_amount(pmt.amount), st["right"]),
            ])
            pri += 1
    else:
        pdata.append([Paragraph("  No payments received this period", st["muted"]), "", ""])
        pcmds.append(("SPAN", (0, pri), (2, pri)))
        pri += 1

    pdata.append([Paragraph("Total Payments Received", st["bold"]),
                  "",
                  Paragraph(_fmt_amount(bill.summary.payments_received), st["rbold"])])
    pcmds += [("LINEABOVE",  (0, pri), (-1, pri), 0.5, L.BOX_BORDER),
              ("TOPPADDING", (0, pri), (-1, pri), 4)]

    dw = _DESC_W - _DATE_W
    pmt_table = Table(pdata, colWidths=[dw, _DATE_W, _AMT_W], splitByRow=True)
    pmt_table.setStyle(TableStyle(pcmds))
    story.append(pmt_table)

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
