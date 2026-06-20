"""
PDF renderer for the SLT E-Bill INVOICE layout.
Accepts a validated Bill object from the billing engine; never reads from the DB directly.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

# Side-effect import: registers Noto fonts with ReportLab's font registry
from app.pdf import layout as L
from app.pdf.barcodes import draw_barcode, draw_qr
from app.billing.schemas import Bill

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_amount(d: Decimal) -> str:
    """Decimal → "1,154.84" (or "-250.00" for negatives)."""
    return f"{d:,.2f}"


def _fmt_date(d: date) -> str:
    """date → "25/02/2024"."""
    return d.strftime("%d/%m/%Y")


def _period_str(period_start: date | None, period_end: date | None) -> str:
    if period_start and period_end:
        return f"{_fmt_date(period_start)} - {_fmt_date(period_end)}"
    return ""


# ---------------------------------------------------------------------------
# Page / slip geometry
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = A4          # 595.28 × 841.89 pt
MARGIN    = L.MARGIN         # 36
LEFT      = L.LEFT           # 36
RIGHT     = L.RIGHT          # 559.28
CONTENT_W = L.CONTENT_W      # 523.28

HEADER_H  = 70.0
SLIP_H    = 132.0
SLIP_Y    = MARGIN           # slip bottom  (y = 36)
SLIP_TOP  = SLIP_Y + SLIP_H  # dashed line  (y = 168)
LEGAL_Y   = SLIP_TOP + 14   # legal text   (y = 182)


# ---------------------------------------------------------------------------
# A. Header band  (no bill data — SLT company info is constant)
# ---------------------------------------------------------------------------
def _draw_header(c: rl_canvas.Canvas) -> None:
    y = PAGE_H - HEADER_H
    c.setFillColor(L.HEADER_BLUE)
    c.rect(0, y, PAGE_W, HEADER_H, stroke=0, fill=1)

    c.setFont("Noto-Bold", 22)
    c.setFillColor(L.WHITE)
    c.drawString(LEFT, y + 34, "INVOICE")

    c.setFont("Noto", 7)
    c.drawString(LEFT, y + 21, "Sri Lanka Telecom PLC")
    c.drawString(LEFT, y + 12, "Lotus Road, P.O Box 503, Colombo 01.")

    logo_h = HEADER_H - 14.0
    logo_w = 140.0
    logo_x = RIGHT - logo_w
    logo_y = y + (HEADER_H - logo_h) / 2
    try:
        c.drawImage(L.LOGO_PATH, logo_x, logo_y,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, anchor="c", mask="auto")
    except Exception:
        c.setFont("Noto-Bold", 10)
        c.setFillColor(L.WHITE)
        c.drawRightString(RIGHT, y + 30, "SLT MOBITEL")


# ---------------------------------------------------------------------------
# B. Identity block  (two columns)
# ---------------------------------------------------------------------------
def _draw_identity(c: rl_canvas.Canvas, bill: Bill, top_y: float) -> float:
    """Account fields (left) + customer / barcode / QR (right). Returns bottom y."""
    y = top_y - 10

    left_w  = CONTENT_W * 0.44
    right_x = LEFT + left_w + 10
    right_w = CONTENT_W - left_w - 10

    # ── Left column ──────────────────────────────────────────────────────────
    c.setFont("Noto", 6.5)
    c.setFillColor(L.LABEL_BLUE)
    c.drawString(LEFT, y, "TELEPHONE NUMBER")
    c.setFont("Noto-Bold", 9)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT + 96, y, bill.telephone_number or "")
    y -= 6

    ROW_H   = 15.0
    ROW_GAP = 5.0

    def left_field(label: str, value: str) -> None:
        nonlocal y
        y -= (ROW_H + ROW_GAP)
        L.draw_field_box(c, label, value, LEFT, y, left_w, h=ROW_H)

    left_field("Account Number", bill.account_number)
    left_field("Invoice Number",  bill.invoice_number)
    left_field("Billing Date",    _fmt_date(bill.billing_date))
    left_field("Billing Period",  _period_str(bill.period_start, bill.period_end))

    bottom_left = y

    # ── Right column ─────────────────────────────────────────────────────────
    ry = top_y - 10

    c.setFont("Noto", 7)
    c.setFillColor(L.MUTED_COLOR)
    c.drawRightString(RIGHT, ry, "1 of 1")
    ry -= 5

    # Customer box
    cust_h = 58.0
    ry -= cust_h
    c.setStrokeColor(L.GREEN_BORDER)
    c.setLineWidth(1.0)
    c.setFillColor(L.LIGHT_GREY)
    c.rect(right_x, ry, right_w, cust_h, stroke=1, fill=1)

    c.setFont("Noto", 7)
    c.setFillColor(L.MUTED_COLOR)
    c.drawString(right_x + 5, ry + cust_h - 11, "Rev. Mr / Mrs.")

    c.setFont("Noto-Bold", 9)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(right_x + 5, ry + cust_h - 23, bill.customer_name)

    c.setFont("Noto", 8)
    addr_y = ry + cust_h - 36
    for line in bill.address_lines:
        c.drawString(right_x + 5, addr_y, line)
        addr_y -= 11

    # Service-label banner
    ry -= 5
    banner_h = 14.0
    ry -= banner_h
    c.setFillColor(L.TEAL_FILL)
    c.rect(right_x, ry, right_w, banner_h, stroke=0, fill=1)
    c.setFont("Noto-Bold", 8)
    c.setFillColor(L.WHITE)
    c.drawString(right_x + 6, ry + 3, (bill.service_label or "").upper())

    # Barcode
    ry -= 5
    bc_h = 24.0
    ry -= bc_h
    draw_barcode(c, bill.invoice_number, right_x, ry, w=right_w * 0.72, h=bc_h)

    # QR code
    qr_size = 40.0
    ry -= 6
    ry -= qr_size
    draw_qr(c,
            f"https://www.slt.lk/payonline?inv={bill.invoice_number}",
            right_x, ry, size=qr_size)
    c.setFont("Noto", 6.5)
    c.setFillColor(L.MUTED_COLOR)
    c.drawString(right_x + qr_size + 5, ry + qr_size / 2, "www.slt.lk/payonline")

    return min(bottom_left, ry) - 8


# ---------------------------------------------------------------------------
# C. Summary of Invoice
# ---------------------------------------------------------------------------
def _draw_summary(c: rl_canvas.Canvas, bill: Bill, top_y: float) -> float:
    """Five rounded summary boxes. Returns bottom y."""
    y = top_y - 6

    c.setFont("Noto-Bold", 8.5)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT, y, "SUMMARY OF INVOICE")
    y -= 6

    BOX_H = 54.0
    OP_W  = 14.0
    box_w = (CONTENT_W - 4 * OP_W) / 5.0

    boxes = [
        ("ශේෂ ගෙනෙන",         "Balance B/F",            _fmt_amount(bill.summary.balance_bf),          False),
        ("ලැබුණු ගෙවීම්",      "Payments received",      _fmt_amount(bill.summary.payments_received),   False),
        ("කාල සීමාවේ ගාස්තු", "Charges for the period", _fmt_amount(bill.summary.charges_for_period),  False),
        ("ගෙවිය යුතු මුළු",    "Total payable",          _fmt_amount(bill.summary.total_payable),       True),
        ("ගෙවීමේ දිනය",        "Payment due date",       _fmt_date(bill.due_date),                      True),
    ]
    operators = ["−", "+", "="]

    y -= BOX_H
    bx = LEFT
    for i, (si, en, val, teal) in enumerate(boxes):
        fill_c  = L.TEAL_FILL if teal else L.WHITE
        label_c = L.WHITE     if teal else L.LABEL_BLUE
        muted_c = L.WHITE     if teal else L.MUTED_COLOR
        value_c = L.WHITE     if teal else L.TEXT_COLOR

        c.setFillColor(fill_c)
        c.setStrokeColor(L.TEAL_BORDER)
        c.setLineWidth(0.8)
        c.roundRect(bx, y, box_w, BOX_H, 4, stroke=1, fill=1)

        c.setFont("NotoSinhala", 6.0)
        c.setFillColor(label_c)
        c.drawString(bx + 4, y + BOX_H - 12, si)

        c.setFont("Noto", 6.0)
        c.setFillColor(muted_c)
        c.drawString(bx + 4, y + BOX_H - 22, en)

        c.setFont("Noto-Bold", 10)
        c.setFillColor(value_c)
        c.drawString(bx + 4, y + 8, val)

        if i < 3:
            op_x = bx + box_w + OP_W / 2 - 4
            c.setFont("Noto-Bold", 9)
            c.setFillColor(L.TEXT_COLOR)
            c.drawString(op_x, y + BOX_H / 2 - 5, operators[i])

        bx += box_w + OP_W

    return y - 10


# ---------------------------------------------------------------------------
# D. Details of Charges for the Period
# ---------------------------------------------------------------------------
def _draw_charges(c: rl_canvas.Canvas, bill: Bill, top_y: float) -> float:
    """Grouped service lines + taxes + total. Returns bottom y."""
    y   = top_y
    LH  = 13.0
    IND = 10.0
    AX  = RIGHT

    L.hrule(c, LEFT, y, CONTENT_W, color=L.BOX_BORDER)
    y -= 13

    c.setFont("Noto-Bold", 8.5)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT, y, "DETAILS OF CHARGES FOR THE PERIOD")
    c.setFont("Noto", 7.5)
    c.setFillColor(L.MUTED_COLOR)
    c.drawRightString(AX, y, "(Rs.)")
    y -= LH

    def row(text: str, amount: str | None,
            bold: bool = False, indent: float = 0.0) -> None:
        nonlocal y
        c.setFont("Noto-Bold" if bold else "Noto", 8.0)
        c.setFillColor(L.TEXT_COLOR)
        c.drawString(LEFT + indent, y, text)
        if amount is not None:
            c.drawRightString(AX, y, amount)
        y -= LH

    for grp in bill.groups:
        row(grp.service_number, None, bold=True)
        for li in grp.lines:
            period = _period_str(li.period_start, li.period_end)
            label  = f"{li.description}  [{period}]" if period else li.description
            row(label, _fmt_amount(li.amount), indent=IND)
        y -= 2

    if bill.tax_lines:
        row("Taxes & Levies", None, bold=True)
        for li in bill.tax_lines:
            row(li.description, _fmt_amount(li.amount), indent=IND)

    y -= 2
    L.hrule(c, LEFT, y + LH, CONTENT_W)
    row("Total Charges for the Period",
        _fmt_amount(bill.summary.charges_for_period), bold=True)

    return y - 6


# ---------------------------------------------------------------------------
# E. Details of Payments Received
# ---------------------------------------------------------------------------
def _draw_payments(c: rl_canvas.Canvas, bill: Bill, top_y: float) -> float:
    """Payment rows + total. Returns bottom y."""
    y  = top_y
    LH = 13.0
    AX = RIGHT

    c.setFont("Noto-Bold", 8.5)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT, y, "Details of Payments Received")
    y -= LH

    if bill.payments:
        for pmt in bill.payments:
            label = pmt.reference or pmt.method
            c.setFont("Noto", 8.0)
            c.setFillColor(L.TEXT_COLOR)
            c.drawString(LEFT + 6, y, label)
            c.drawString(LEFT + 170, y, _fmt_date(pmt.payment_date))
            c.drawRightString(AX, y, _fmt_amount(pmt.amount))
            y -= LH
    else:
        c.setFont("Noto", 8.0)
        c.setFillColor(L.MUTED_COLOR)
        c.drawString(LEFT + 6, y, "No payments received this period")
        y -= LH

    L.hrule(c, LEFT, y + LH - 2, CONTENT_W)
    c.setFont("Noto-Bold", 8.0)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT, y, "Total Payments Received")
    c.drawRightString(AX, y, _fmt_amount(bill.summary.payments_received))
    y -= LH

    return y - 8


# ---------------------------------------------------------------------------
# G. Legal line (fixed position above the payment slip)
# ---------------------------------------------------------------------------
def _draw_legal(c: rl_canvas.Canvas) -> None:
    text = (
        "This electronic form of the bill has the same legal recognition, effect, validity or "
        "enforceability as the original form of the bill, in terms of the Electronic Transactions "
        "Act No.19 of 2006."
    )
    c.setFont("Noto", 6)
    c.setFillColor(L.MUTED_COLOR)
    mid = len(text) // 2
    cut = text.rfind(" ", 0, mid)
    c.drawString(LEFT, LEGAL_Y + 9, text[:cut])
    c.drawString(LEFT, LEGAL_Y,     text[cut + 1:])


# ---------------------------------------------------------------------------
# I. Tear-off payment slip (anchored to page bottom)
# ---------------------------------------------------------------------------
def _draw_payment_slip(c: rl_canvas.Canvas, bill: Bill) -> None:
    sep_y = SLIP_TOP

    c.setDash(4, 3)
    c.setStrokeColor(L.MUTED_COLOR)
    c.setLineWidth(0.5)
    c.line(0, sep_y, PAGE_W, sep_y)
    c.setDash()

    c.setFillColor(L.WHITE)
    c.rect(0, SLIP_Y, PAGE_W, SLIP_H, stroke=0, fill=1)

    c.setFont("Noto-Bold", 9)
    c.setFillColor(L.HEADER_BLUE)
    c.drawString(LEFT, sep_y - 14, "Payment Slip")

    # ── Left field grid ──────────────────────────────────────────────────────
    lw    = CONTENT_W * 0.52
    FH    = 13.0
    FG    = 3.5
    LBL_W = 68.0

    slip_fields = [
        ("Telephone No.",  bill.telephone_number or ""),
        ("Invoice No.",    bill.invoice_number),
        ("Customer Name",  bill.customer_name),
        ("Account No.",    bill.account_number),
        ("Amount (Rs.)",   _fmt_amount(bill.summary.total_payable)),
    ]

    fy = sep_y - 20
    for label, val in slip_fields:
        fy -= FH
        c.setFillColor(L.HEADER_BLUE)
        c.rect(LEFT, fy, LBL_W, FH, stroke=0, fill=1)
        c.setFont("Noto", 5.5)
        c.setFillColor(L.WHITE)
        c.drawString(LEFT + 2, fy + 3, label)
        val_w = lw - LBL_W
        c.setFillColor(L.LIGHT_GREY)
        c.setStrokeColor(L.BOX_BORDER)
        c.setLineWidth(0.4)
        c.rect(LEFT + LBL_W, fy, val_w, FH, stroke=1, fill=1)
        c.setFont("Noto", 7.5)
        c.setFillColor(L.TEXT_COLOR)
        c.drawString(LEFT + LBL_W + 3, fy + 3, val)
        fy -= FG

    # ── Right section ────────────────────────────────────────────────────────
    rx = LEFT + lw + 10
    rw = CONTENT_W - lw - 10
    ry = sep_y - 20

    bc_h = 25.0
    ry -= bc_h
    draw_barcode(c, bill.invoice_number, rx, ry, w=rw * 0.74, h=bc_h)

    ry -= 16
    cx = rx
    for lbl in ("Cash", "Cheques", "Credit Card"):
        c.setStrokeColor(L.TEXT_COLOR)
        c.setLineWidth(0.5)
        c.rect(cx, ry + 1, 8, 8, stroke=1, fill=0)
        c.setFont("Noto", 6.5)
        c.setFillColor(L.TEXT_COLOR)
        c.drawString(cx + 11, ry + 2, lbl)
        cx += 55

    qr_size = 38.0
    ry -= 7
    ry -= qr_size
    qr_x = rx + rw - qr_size
    draw_qr(c,
            f"https://www.slt.lk/payonline?inv={bill.invoice_number}",
            qr_x, ry, size=qr_size)
    c.setFont("Noto", 5.5)
    c.setFillColor(L.MUTED_COLOR)
    c.drawCentredString(qr_x + qr_size / 2, ry - 8, "LANKAQR")

    try:
        c.drawImage(L.LOGO_PATH, rx, ry + 8,
                    width=52, height=22,
                    preserveAspectRatio=True, mask="auto")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def render_bill(bill: Bill, out_path: str | None = None) -> str:
    """Render a validated Bill to a PDF. Returns the path written."""
    if out_path is None:
        out_dir = Path("output")
        out_dir.mkdir(exist_ok=True)
        safe = bill.account_number.replace(" ", "-")
        out_path = str(out_dir / f"{safe}_{bill.period_start}_{bill.period_end}.pdf")

    c = rl_canvas.Canvas(out_path, pagesize=A4)

    _draw_header(c)
    y = _draw_identity(c, bill, PAGE_H - HEADER_H)
    y = _draw_summary(c, bill, y)
    y = _draw_charges(c, bill, y)
    _draw_payments(c, bill, y)
    _draw_legal(c)
    _draw_payment_slip(c, bill)

    c.showPage()
    c.save()
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
