"""
PDF renderer for the SLT E-Bill INVOICE layout.
Step 5: all values are hard-coded to Sample-1 from docs/DATABASE.md §7.
Step 6 will replace the constants with fields from a Bill object.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

# Side-effect import: registers Noto fonts with ReportLab's font registry
from app.pdf import layout as L
from app.pdf.barcodes import draw_barcode, draw_qr

# ---------------------------------------------------------------------------
# Hard-coded Sample-1 data  (Step 5 only — wired to Bill object in Step 6)
# ---------------------------------------------------------------------------
_ACCOUNT    = "004 152 4075"
_TELEPHONE  = "0359236535"
_SVC_LABEL  = "LTE SERVICE"
_CUSTOMER   = "Pavithim Nayapila Senadira"
_ADDRESS    = ["No 807/102 Welimada Road", "Badulla 90200"]
_INV_NUM    = "0038474527-0337"
_BILL_DATE  = "25/02/2024"
_PERIOD     = "24/01/2024 - 23/02/2024"
_DUE_DATE   = "17/03/2024"

_BAL_BF     = "7,703.28"
_PMTS_REC   = "5,000.00"
_CHGS_PERIOD = "1,925.24"
_TOTAL_PAY  = "4,628.52"

_GROUPS = [
    {
        "service_number": "0359236535",
        "label": "SLT Voice Service 4G Net pal",
        "lines": [
            ("SLT Voice Service 4G Net pal [Rental]",  "24/01/2024 - 16/02/2024", "0.00"),
            ("SLT Voice Service 4G Net pal [Rental]",  "17/02/2024 - 23/02/2024", "0.00"),
        ],
    },
    {
        "service_number": "940359236535",
        "label": "SLT BroadBand Service LTE Web Family Plus",
        "lines": [
            ("SLT BroadBand Service LTE Web Family Plus [Rental]", "24/01/2024 - 12/02/2024", "1,154.84"),
            ("SLT BroadBand Service LTE Web Family Plus [Rental]", "17/02/2024 - 23/02/2024",   "404.19"),
        ],
    },
]
_TAX_LINES  = [("Taxes & Levies", "366.21")]
_CHGS_TOTAL = "1,559.03"
_TAXES_TOT  = "366.21"

_PAYMENTS   = [("Physical payment", "16/02/2024", "5,000.00")]
_PMTS_TOTAL = "5,000.00"

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
# A. Header band
# ---------------------------------------------------------------------------
def _draw_header(c: rl_canvas.Canvas) -> None:
    y = PAGE_H - HEADER_H
    c.setFillColor(L.HEADER_BLUE)
    c.rect(0, y, PAGE_W, HEADER_H, stroke=0, fill=1)

    # "INVOICE" word-mark
    c.setFont("Noto-Bold", 22)
    c.setFillColor(L.WHITE)
    c.drawString(LEFT, y + 34, "INVOICE")

    # Company address block
    c.setFont("Noto", 7)
    c.drawString(LEFT, y + 21, "Sri Lanka Telecom PLC")
    c.drawString(LEFT, y + 12, "Lotus Road, P.O Box 503, Colombo 01.")

    # Logo — right side
    logo_w, logo_h = 100.0, 42.0
    logo_x = RIGHT - logo_w
    logo_y = y + (HEADER_H - logo_h) / 2
    try:
        c.drawImage(L.LOGO_PATH, logo_x, logo_y,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask="auto")
    except Exception:
        c.setFont("Noto-Bold", 10)
        c.drawRightString(RIGHT, y + 30, "SLT MOBITEL")

    # "The Connection" byline below logo
    c.setFont("Noto", 6)
    c.setFillColor(L.WHITE)
    c.drawRightString(RIGHT, y + 5, "The Connection")


# ---------------------------------------------------------------------------
# B. Identity block  (two columns)
# ---------------------------------------------------------------------------
def _draw_identity(c: rl_canvas.Canvas, top_y: float) -> float:
    """Account info (left) + customer / barcode / QR (right). Returns bottom y."""
    y = top_y - 10

    left_w  = CONTENT_W * 0.44          # ≈ 230 pt
    right_x = LEFT + left_w + 10
    right_w = CONTENT_W - left_w - 10   # ≈ 283 pt

    # ── Left column ──────────────────────────────────────────────────────────
    # TELEPHONE NUMBER — caption + inline value (no box)
    c.setFont("Noto", 6.5)
    c.setFillColor(L.LABEL_BLUE)
    c.drawString(LEFT, y, "TELEPHONE NUMBER")
    c.setFont("Noto-Bold", 9)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT + 96, y, _TELEPHONE)
    y -= 6

    ROW_H = 15.0
    ROW_GAP = 5.0

    def left_field(label: str, value: str) -> None:
        nonlocal y
        y -= (ROW_H + ROW_GAP)
        L.draw_field_box(c, label, value, LEFT, y, left_w, h=ROW_H)

    left_field("Account Number", _ACCOUNT)
    left_field("Invoice Number",  _INV_NUM)
    left_field("Billing Date",    _BILL_DATE)
    left_field("Billing Period",  _PERIOD)

    bottom_left = y  # bottom of last left-column field

    # ── Right column ─────────────────────────────────────────────────────────
    ry = top_y - 10

    # "1 of 1" top-right
    c.setFont("Noto", 7)
    c.setFillColor(L.MUTED_COLOR)
    c.drawRightString(RIGHT, ry, "1 of 1")
    ry -= 5

    # Customer box (green border)
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
    c.drawString(right_x + 5, ry + cust_h - 23, _CUSTOMER)

    c.setFont("Noto", 8)
    addr_y = ry + cust_h - 36
    for line in _ADDRESS:
        c.drawString(right_x + 5, addr_y, line)
        addr_y -= 11

    # Service-label banner (teal bar)
    ry -= 5
    banner_h = 14.0
    ry -= banner_h
    c.setFillColor(L.TEAL_FILL)
    c.rect(right_x, ry, right_w, banner_h, stroke=0, fill=1)
    c.setFont("Noto-Bold", 8)
    c.setFillColor(L.WHITE)
    c.drawString(right_x + 6, ry + 3, _SVC_LABEL)

    # Barcode (Code-128 of invoice number)
    ry -= 5
    bc_h = 24.0
    ry -= bc_h
    draw_barcode(c, _INV_NUM, right_x, ry, w=right_w * 0.72, h=bc_h)

    # QR code + pay URL
    qr_size = 40.0
    ry -= 6
    ry -= qr_size
    draw_qr(c,
            f"https://www.slt.lk/payonline?inv={_INV_NUM}",
            right_x, ry, size=qr_size)
    c.setFont("Noto", 6.5)
    c.setFillColor(L.MUTED_COLOR)
    c.drawString(right_x + qr_size + 5, ry + qr_size / 2, "www.slt.lk/payonline")

    return min(bottom_left, ry) - 8


# ---------------------------------------------------------------------------
# C. Summary of Invoice
# ---------------------------------------------------------------------------
def _draw_summary(c: rl_canvas.Canvas, top_y: float) -> float:
    """Five rounded boxes in a row. Returns bottom y."""
    y = top_y - 6

    c.setFont("Noto-Bold", 8.5)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT, y, "SUMMARY OF INVOICE")
    y -= 6

    BOX_H = 54.0
    OP_W  = 14.0
    box_w = (CONTENT_W - 4 * OP_W) / 5.0   # ≈ 93.5 pt

    # (sinhala_caption, english_caption, value, teal_background)
    boxes = [
        ("ශේෂ ගෙනෙන",         "Balance B/F",            _BAL_BF,      False),
        ("ලැබුණු ගෙවීම්",      "Payments received",      _PMTS_REC,    False),
        ("කාල සීමාවේ ගාස්තු", "Charges for the period", _CHGS_PERIOD, False),
        ("ගෙවිය යුතු මුළු",    "Total payable",          _TOTAL_PAY,   True),
        ("ගෙවීමේ දිනය",        "Payment due date",       _DUE_DATE,    True),
    ]
    operators = ["−", "+", "="]   # between boxes 0-1, 1-2, 2-3

    y -= BOX_H
    bx = LEFT
    for i, (si, en, val, teal) in enumerate(boxes):
        fill_c   = L.TEAL_FILL if teal else L.WHITE
        label_c  = L.WHITE     if teal else L.LABEL_BLUE
        muted_c  = L.WHITE     if teal else L.MUTED_COLOR
        value_c  = L.WHITE     if teal else L.TEXT_COLOR

        c.setFillColor(fill_c)
        c.setStrokeColor(L.TEAL_BORDER)
        c.setLineWidth(0.8)
        c.roundRect(bx, y, box_w, BOX_H, 4, stroke=1, fill=1)

        # Sinhala caption (small, top of box)
        c.setFont("NotoSinhala", 6.0)
        c.setFillColor(label_c)
        c.drawString(bx + 4, y + BOX_H - 12, si)

        # English caption
        c.setFont("Noto", 6.0)
        c.setFillColor(muted_c)
        c.drawString(bx + 4, y + BOX_H - 22, en)

        # Value (bottom of box)
        c.setFont("Noto-Bold", 10)
        c.setFillColor(value_c)
        c.drawString(bx + 4, y + 8, val)

        # Operator in the gap to the right (only for first 3 boxes)
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
def _draw_charges(c: rl_canvas.Canvas, top_y: float) -> float:
    """Grouped service lines + taxes + total. Returns bottom y."""
    y   = top_y
    LH  = 13.0          # line height
    IND = 10.0          # indent for child rows
    AX  = RIGHT         # right-align x for amounts

    L.hrule(c, LEFT, y, CONTENT_W, color=L.BOX_BORDER)
    y -= 13

    c.setFont("Noto-Bold", 8.5)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT, y, "DETAILS OF CHARGES FOR THE PERIOD")
    c.setFont("Noto", 7.5)
    c.setFillColor(L.MUTED_COLOR)
    c.drawRightString(AX, y, "(Rs.)")
    y -= LH

    def row(text: str, amount: str | None, bold: bool = False, indent: float = 0.0) -> None:
        nonlocal y
        c.setFont("Noto-Bold" if bold else "Noto", 8.0)
        c.setFillColor(L.TEXT_COLOR)
        c.drawString(LEFT + indent, y, text)
        if amount is not None:
            c.setFont("Noto-Bold" if bold else "Noto", 8.0)
            c.drawRightString(AX, y, amount)
        y -= LH

    # Grouped charge lines
    for grp in _GROUPS:
        row(grp["service_number"], None, bold=True)
        for desc, period, amt in grp["lines"]:
            row(f"{desc}  [{period}]", amt, indent=IND)
        y -= 2

    # Taxes & Levies
    row("Taxes & Levies", None, bold=True)
    for desc, amt in _TAX_LINES:
        row(desc, amt, indent=IND)

    # Separator + grand total
    y -= 2
    L.hrule(c, LEFT, y + LH, CONTENT_W)
    row("Total Charges for the Period", _CHGS_PERIOD, bold=True)

    return y - 6


# ---------------------------------------------------------------------------
# E. Details of Payments Received
# ---------------------------------------------------------------------------
def _draw_payments(c: rl_canvas.Canvas, top_y: float) -> float:
    """Payment rows + total. Returns bottom y."""
    y  = top_y
    LH = 13.0
    AX = RIGHT

    c.setFont("Noto-Bold", 8.5)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT, y, "Details of Payments Received")
    y -= LH

    for desc, dt, amt in _PAYMENTS:
        c.setFont("Noto", 8.0)
        c.setFillColor(L.TEXT_COLOR)
        c.drawString(LEFT + 6, y, desc)
        c.drawString(LEFT + 170, y, dt)
        c.drawRightString(AX, y, amt)
        y -= LH

    L.hrule(c, LEFT, y + LH - 2, CONTENT_W)
    c.setFont("Noto-Bold", 8.0)
    c.drawString(LEFT, y, "Total Payments Received")
    c.drawRightString(AX, y, _PMTS_TOTAL)
    y -= LH

    return y - 8


# ---------------------------------------------------------------------------
# G. Legal line (fixed position above slip)
# ---------------------------------------------------------------------------
def _draw_legal(c: rl_canvas.Canvas) -> None:
    text = (
        "This electronic form of the bill has the same legal recognition, effect, validity or "
        "enforceability as the original form of the bill, in terms of the Electronic Transactions "
        "Act No.19 of 2006."
    )
    c.setFont("Noto", 6)
    c.setFillColor(L.MUTED_COLOR)
    # Naive word-wrap into two lines
    mid = len(text) // 2
    cut = text.rfind(" ", 0, mid)
    c.drawString(LEFT, LEGAL_Y + 9, text[:cut])
    c.drawString(LEFT, LEGAL_Y,     text[cut + 1:])


# ---------------------------------------------------------------------------
# I. Tear-off payment slip (anchored to page bottom)
# ---------------------------------------------------------------------------
def _draw_payment_slip(c: rl_canvas.Canvas) -> None:
    sep_y = SLIP_TOP   # y of the dashed separator

    # Dashed separator line
    c.setDash(4, 3)
    c.setStrokeColor(L.MUTED_COLOR)
    c.setLineWidth(0.5)
    c.line(0, sep_y, PAGE_W, sep_y)
    c.setDash()

    # Slip background
    c.setFillColor(L.WHITE)
    c.rect(0, SLIP_Y, PAGE_W, SLIP_H, stroke=0, fill=1)

    # "Payment Slip" heading
    c.setFont("Noto-Bold", 9)
    c.setFillColor(L.HEADER_BLUE)
    c.drawString(LEFT, sep_y - 14, "Payment Slip")

    # ── Left field grid ──────────────────────────────────────────────────────
    lw    = CONTENT_W * 0.52          # left-section width ≈ 272 pt
    FH    = 13.0                       # field height
    FG    = 3.5                        # gap between fields
    LBL_W = 68.0                       # blue label box width

    slip_fields = [
        ("Telephone No.",  _TELEPHONE),
        ("Invoice No.",    _INV_NUM),
        ("Customer Name",  _CUSTOMER),
        ("Account No.",    _ACCOUNT),
        ("Amount (Rs.)",   _TOTAL_PAY),
    ]

    fy = sep_y - 20
    for label, val in slip_fields:
        fy -= FH
        # Blue label box
        c.setFillColor(L.HEADER_BLUE)
        c.rect(LEFT, fy, LBL_W, FH, stroke=0, fill=1)
        c.setFont("Noto", 5.5)
        c.setFillColor(L.WHITE)
        c.drawString(LEFT + 2, fy + 3, label)
        # Value box
        val_w = lw - LBL_W
        c.setFillColor(L.LIGHT_GREY)
        c.setStrokeColor(L.BOX_BORDER)
        c.setLineWidth(0.4)
        c.rect(LEFT + LBL_W, fy, val_w, FH, stroke=1, fill=1)
        c.setFont("Noto", 7.5)
        c.setFillColor(L.TEXT_COLOR)
        c.drawString(LEFT + LBL_W + 3, fy + 3, val)
        fy -= FG

    # ── Right section: barcode + checkboxes + QR + logo ─────────────────────
    rx  = LEFT + lw + 10
    rw  = CONTENT_W - lw - 10
    ry  = sep_y - 20

    # Barcode
    bc_h = 25.0
    ry  -= bc_h
    draw_barcode(c, _INV_NUM, rx, ry, w=rw * 0.74, h=bc_h)

    # Checkboxes
    ry -= 16
    cx = rx
    for label in ("Cash", "Cheques", "Credit Card"):
        c.setStrokeColor(L.TEXT_COLOR)
        c.setLineWidth(0.5)
        c.rect(cx, ry + 1, 8, 8, stroke=1, fill=0)
        c.setFont("Noto", 6.5)
        c.setFillColor(L.TEXT_COLOR)
        c.drawString(cx + 11, ry + 2, label)
        cx += 55

    # QR code (bottom-right of slip)
    qr_size = 38.0
    ry -= 7
    ry -= qr_size
    qr_x = rx + rw - qr_size
    draw_qr(c,
            f"https://www.slt.lk/payonline?inv={_INV_NUM}",
            qr_x, ry, size=qr_size)
    c.setFont("Noto", 5.5)
    c.setFillColor(L.MUTED_COLOR)
    c.drawCentredString(qr_x + qr_size / 2, ry - 8, "LANKAQR")

    # SLT logo (small, beside QR)
    try:
        c.drawImage(L.LOGO_PATH, rx, ry + 8,
                    width=52, height=22,
                    preserveAspectRatio=True, mask="auto")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def render_sample1(out_path: str | None = None) -> str:
    """Render the hard-coded Sample-1 bill. Returns the path of the PDF written."""
    if out_path is None:
        out_dir = Path("output")
        out_dir.mkdir(exist_ok=True)
        out_path = str(out_dir / "sample1_004-152-4075_2024-01-24_2024-02-23.pdf")

    c = rl_canvas.Canvas(out_path, pagesize=A4)

    _draw_header(c)

    identity_top = PAGE_H - HEADER_H
    y = _draw_identity(c, identity_top)
    y = _draw_summary(c, y)
    y = _draw_charges(c, y)
    y = _draw_payments(c, y)

    _draw_legal(c)
    _draw_payment_slip(c)

    c.showPage()
    c.save()
    return out_path


if __name__ == "__main__":
    path = render_sample1()
    print(f"PDF written: {path}")
