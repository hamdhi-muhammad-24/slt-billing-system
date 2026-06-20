"""
PDF renderer for the SLT E-Bill INVOICE layout.
Accepts a validated Bill object; never reads from the DB directly.

Step 7: sections D+E use platypus flowables so long bills paginate.
        Continuation pages repeat a slim header.
        Every page carries "Page X of N" via NumberedCanvas.
        Payment slip + legal notice live in _SlipFlowable, the last item
        in the story, so they always appear at the very bottom of the last page.
"""
from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

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
PAGE_W, PAGE_H = A4
MARGIN    = L.MARGIN
LEFT      = L.LEFT
RIGHT     = L.RIGHT
CONTENT_W = L.CONTENT_W

HEADER_H  = 70.0
SLIM_H    = 30.0   # slim repeat-header height on continuation pages


# ---------------------------------------------------------------------------
# NumberedCanvas — defers showPage so "Page X of N" can be painted last
# ---------------------------------------------------------------------------
class _NumberedCanvas(rl_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved: list[dict] = []

    def showPage(self) -> None:                   # called by platypus per page
        self._saved.append(dict(self.__dict__))   # shallow-copy current state
        self._startPage()                         # reset for next page

    def save(self) -> None:
        n = len(self._saved)
        for i, state in enumerate(self._saved):
            self.__dict__.update(state)
            _paint_page_number(self, i + 1, n)
            super().showPage()
        super().save()


def _paint_page_number(c: rl_canvas.Canvas, page: int, total: int) -> None:
    text = f"Page {page} of {total}"
    c.setFont("Noto", 7)
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

    c.setFont("Noto-Bold", 22)
    c.setFillColor(L.WHITE)
    c.drawString(LEFT, y + 34, "INVOICE")

    c.setFont("Noto", 7)
    c.drawString(LEFT, y + 21, "Sri Lanka Telecom PLC")
    c.drawString(LEFT, y + 12, "Lotus Road, P.O Box 503, Colombo 01.")

    logo_h = HEADER_H - 14.0
    logo_w = 140.0
    try:
        c.drawImage(L.LOGO_PATH, RIGHT - logo_w, y + (HEADER_H - logo_h) / 2,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, anchor="c", mask="auto")
    except Exception:
        c.setFont("Noto-Bold", 10)
        c.setFillColor(L.WHITE)
        c.drawRightString(RIGHT, y + 30, "SLT MOBITEL")


# ---------------------------------------------------------------------------
# Slim header band (continuation pages)
# ---------------------------------------------------------------------------
def _draw_slim_header(c: rl_canvas.Canvas) -> None:
    y = PAGE_H - SLIM_H
    c.setFillColor(L.HEADER_BLUE)
    c.rect(0, y, PAGE_W, SLIM_H, stroke=0, fill=1)

    c.setFont("Noto-Bold", 9)
    c.setFillColor(L.WHITE)
    c.drawString(LEFT, y + 10, "INVOICE — Continued")

    try:
        c.drawImage(L.LOGO_PATH, RIGHT - 75, y + 2,
                    width=75, height=24,
                    preserveAspectRatio=True, anchor="c", mask="auto")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# B. Identity block
# ---------------------------------------------------------------------------
def _draw_identity(c: rl_canvas.Canvas, bill: Bill, top_y: float) -> float:
    """Returns the y below the identity block (= top of summary)."""
    y = top_y - 10

    left_w  = CONTENT_W * 0.44
    right_x = LEFT + left_w + 10
    right_w = CONTENT_W - left_w - 10

    # Left column
    c.setFont("Noto", 6.5)
    c.setFillColor(L.LABEL_BLUE)
    c.drawString(LEFT, y, "TELEPHONE NUMBER")
    c.setFont("Noto-Bold", 9)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT + 96, y, bill.telephone_number or "")
    y -= 6

    ROW_H, ROW_GAP = 15.0, 5.0

    def left_field(label: str, value: str) -> None:
        nonlocal y
        y -= ROW_H + ROW_GAP
        L.draw_field_box(c, label, value, LEFT, y, left_w, h=ROW_H)

    left_field("Account Number", bill.account_number)
    left_field("Invoice Number",  bill.invoice_number)
    left_field("Billing Date",    _fmt_date(bill.billing_date))
    left_field("Billing Period",  _period_str(bill.period_start, bill.period_end))
    bottom_left = y

    # Right column
    ry = top_y - 10
    ry -= 5   # gap where "Page X of N" is painted by NumberedCanvas

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

    ry -= 5
    banner_h = 14.0
    ry -= banner_h
    c.setFillColor(L.TEAL_FILL)
    c.rect(right_x, ry, right_w, banner_h, stroke=0, fill=1)
    c.setFont("Noto-Bold", 8)
    c.setFillColor(L.WHITE)
    c.drawString(right_x + 6, ry + 3, (bill.service_label or "").upper())

    ry -= 5
    bc_h = 24.0
    ry -= bc_h
    draw_barcode(c, bill.invoice_number, right_x, ry, w=right_w * 0.72, h=bc_h)

    qr_size = 40.0
    ry -= 6
    ry -= qr_size
    draw_qr(c, f"https://www.slt.lk/payonline?inv={bill.invoice_number}",
            right_x, ry, size=qr_size)
    c.setFont("Noto", 6.5)
    c.setFillColor(L.MUTED_COLOR)
    c.drawString(right_x + qr_size + 5, ry + qr_size / 2, "www.slt.lk/payonline")

    return min(bottom_left, ry) - 8


# ---------------------------------------------------------------------------
# C. Summary of Invoice
# ---------------------------------------------------------------------------
def _draw_summary(c: rl_canvas.Canvas, bill: Bill, top_y: float) -> float:
    """Returns the y below the summary row."""
    y = top_y - 6
    c.setFont("Noto-Bold", 8.5)
    c.setFillColor(L.TEXT_COLOR)
    c.drawString(LEFT, y, "SUMMARY OF INVOICE")
    y -= 6

    BOX_H = 54.0
    OP_W  = 14.0
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
            c.setFont("Noto-Bold", 9)
            c.setFillColor(L.TEXT_COLOR)
            c.drawString(bx + box_w + OP_W / 2 - 4, y + BOX_H / 2 - 5, operators[i])

        bx += box_w + OP_W

    return y - 10


# ---------------------------------------------------------------------------
# Measurement pass — dry-run to find where page-1 content frame starts
# ---------------------------------------------------------------------------
def _measure_frame_top(bill: Bill) -> float:
    """Returns the y coordinate where the content frame starts on page 1."""
    dummy = rl_canvas.Canvas(io.BytesIO(), pagesize=A4)
    _draw_header(dummy)
    y = _draw_identity(dummy, bill, PAGE_H - HEADER_H)
    y = _draw_summary(dummy, bill, y)
    return y


# ---------------------------------------------------------------------------
# I. Payment slip + legal notice — platypus flowable, always last in story
# ---------------------------------------------------------------------------
class _SlipFlowable(Flowable):
    """
    Claims all remaining frame space via wrap().
    Draws (from top to bottom):
      - blank space (pushes content to the bottom)
      - legal notice text
      - dashed tear-off separator (full page width)
      - payment slip content

    Forces a page break when the remaining space is too small, so the slip
    always lands at the very bottom of the last page regardless of page count.

    Coordinates inside draw() are LOCAL (canvas already translated by platypus):
      local (0, 0) = page (LEFT, frame.y1) = page (36, 36)
      local y = SLIP_H = page y = SLIP_H + MARGIN = 168 (top of slip / dashed line)
    """
    _SLIP_H  = 132.0   # height of slip content below the dashed line
    _LEGAL_H = 28.0    # height reserved for the two-line legal notice above the line
    _MIN_H   = _SLIP_H + _LEGAL_H  # 160 pt — minimum frame space needed

    _LEGAL = (
        "This electronic form of the bill has the same legal recognition, effect, validity or "
        "enforceability as the original form of the bill, in terms of the Electronic "
        "Transactions Act No.19 of 2006."
    )

    def __init__(self, bill: Bill) -> None:
        super().__init__()
        self._bill = bill
        self._h    = self._MIN_H   # updated in wrap(); used in draw()

    def wrap(self, availW: float, availH: float):
        if availH < self._MIN_H:
            # Signal "doesn't fit" → platypus inserts a page break and retries
            return (availW, availH + 1)
        self._h = availH
        return (availW, availH)

    def draw(self) -> None:  # noqa: C901
        c   = self.canv
        b   = self._bill
        sh  = self._SLIP_H   # 132 pt — top of slip = local y = 132
        h   = self._h        # all remaining frame space

        # ── Legal notice (just above the dashed line) ─────────────────────
        # local y = sh + 14 → page y = 36 + 146 = 182  (same as old LEGAL_Y)
        mid  = len(self._LEGAL) // 2
        cut  = self._LEGAL.rfind(" ", 0, mid)
        c.setFont("Noto", 6)
        c.setFillColor(L.MUTED_COLOR)
        c.drawString(0, sh + 23, self._LEGAL[:cut])
        c.drawString(0, sh + 14, self._LEGAL[cut + 1:])

        # ── Dashed tear-off separator (full page width) ───────────────────
        # local x: -LEFT to PAGE_W - LEFT  →  page x: 0 to PAGE_W
        c.saveState()
        c.setDash(4, 3)
        c.setStrokeColor(L.MUTED_COLOR)
        c.setLineWidth(0.5)
        c.line(-LEFT, sh, PAGE_W - LEFT, sh)
        c.setDash()
        c.restoreState()

        # ── White background for the slip area ────────────────────────────
        c.setFillColor(L.WHITE)
        c.rect(-LEFT, 0, PAGE_W, sh, stroke=0, fill=1)

        # ── "Payment Slip" heading ────────────────────────────────────────
        c.setFont("Noto-Bold", 9)
        c.setFillColor(L.HEADER_BLUE)
        c.drawString(0, sh - 14, "Payment Slip")

        # ── Left field grid ───────────────────────────────────────────────
        lw    = CONTENT_W * 0.52
        FH    = 13.0
        FG    = 3.5
        LBL_W = 68.0

        slip_fields = [
            ("Telephone No.",  b.telephone_number or ""),
            ("Invoice No.",    b.invoice_number),
            ("Customer Name",  b.customer_name),
            ("Account No.",    b.account_number),
            ("Amount (Rs.)",   _fmt_amount(b.summary.total_payable)),
        ]

        # fy starts at local y = sh - 20 = 112 → page y = 148
        fy = sh - 20
        for label, val in slip_fields:
            fy -= FH
            c.setFillColor(L.HEADER_BLUE)
            c.rect(0, fy, LBL_W, FH, stroke=0, fill=1)
            c.setFont("Noto", 5.5)
            c.setFillColor(L.WHITE)
            c.drawString(2, fy + 3, label)
            val_w = lw - LBL_W
            c.setFillColor(L.LIGHT_GREY)
            c.setStrokeColor(L.BOX_BORDER)
            c.setLineWidth(0.4)
            c.rect(LBL_W, fy, val_w, FH, stroke=1, fill=1)
            c.setFont("Noto", 7.5)
            c.setFillColor(L.TEXT_COLOR)
            c.drawString(LBL_W + 3, fy + 3, val)
            fy -= FG

        # ── Right section (barcode / checkboxes / QR / logo) ─────────────
        # local rx = lw + 10  →  page x = LEFT + lw + 10
        rx = lw + 10
        rw = CONTENT_W - lw - 10
        ry = sh - 20   # local: 112

        bc_h = 25.0
        ry -= bc_h    # 87
        draw_barcode(c, b.invoice_number, rx, ry, w=rw * 0.74, h=bc_h)

        ry -= 16      # 71
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
        ry -= 7        # 64
        ry -= qr_size  # 26
        qr_x = rx + rw - qr_size
        draw_qr(c, f"https://www.slt.lk/payonline?inv={b.invoice_number}",
                 qr_x, ry, size=qr_size)
        c.setFont("Noto", 5.5)
        c.setFillColor(L.MUTED_COLOR)
        c.drawCentredString(qr_x + qr_size / 2, ry - 8, "LANKAQR")

        try:
            c.drawImage(L.LOGO_PATH, rx, ry + 8, width=52, height=22,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Platypus story — sections D (charges) + E (payments) + slip
# ---------------------------------------------------------------------------
_DESC_W = CONTENT_W - 85.0
_AMT_W  = 85.0
_DATE_W = 80.0

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

    # ── D. Details of Charges ────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", color=L.BOX_BORDER, thickness=0.5,
                             spaceAfter=4))

    # Section title row (its own mini-table so "(Rs.)" is right-aligned)
    title_row = Table(
        [[Paragraph("DETAILS OF CHARGES FOR THE PERIOD", st["hdg"]),
          Paragraph("(Rs.)", st["muted"])]],
        colWidths=[_DESC_W, _AMT_W],
    )
    title_row.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN",         (1, 0), (1, 0),  "RIGHT"),
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
    ]))
    story.append(title_row)

    # Charge rows
    data: list[list] = []
    cmds: list       = list(_BASE_TS)
    ri = 0

    for grp in bill.groups:
        data.append([Paragraph(grp.service_number, st["bold"]), ""])
        cmds.append(("TOPPADDING",    (0, ri), (-1, ri), 3))
        cmds.append(("BOTTOMPADDING", (0, ri), (-1, ri), 2))
        ri += 1

        for li in grp.lines:
            period = _period_str(li.period_start, li.period_end)
            label  = f"    {li.description}"
            if period:
                label += f"  [{period}]"
            data.append([Paragraph(label, st["base"]),
                         Paragraph(_fmt_amount(li.amount), st["right"])])
            ri += 1

        # small gap after group
        data.append(["", ""])
        cmds.extend([("TOPPADDING",    (0, ri), (-1, ri), 0),
                     ("BOTTOMPADDING", (0, ri), (-1, ri), 3)])
        ri += 1

    if bill.tax_lines:
        data.append([Paragraph("Taxes &amp; Levies", st["bold"]), ""])
        cmds.append(("TOPPADDING",    (0, ri), (-1, ri), 3))
        ri += 1
        for li in bill.tax_lines:
            data.append([Paragraph(f"    {li.description}", st["base"]),
                         Paragraph(_fmt_amount(li.amount), st["right"])])
            ri += 1

    # gap + total row
    data.append(["", ""])
    cmds.extend([("TOPPADDING",    (0, ri), (-1, ri), 0),
                 ("BOTTOMPADDING", (0, ri), (-1, ri), 0)])
    ri += 1

    data.append([Paragraph("Total Charges for the Period", st["bold"]),
                 Paragraph(_fmt_amount(bill.summary.charges_for_period), st["rbold"])])
    cmds.extend([
        ("LINEABOVE",     (0, ri), (-1, ri), 0.5, L.BOX_BORDER),
        ("TOPPADDING",    (0, ri), (-1, ri), 4),
        ("BOTTOMPADDING", (0, ri), (-1, ri), 2),
    ])

    if data:
        charge_table = Table(data, colWidths=[_DESC_W, _AMT_W], splitByRow=True)
        charge_table.setStyle(TableStyle(cmds))
        story.append(charge_table)

    story.append(Spacer(0, 8))

    # ── E. Details of Payments ───────────────────────────────────────────────
    pdata: list[list] = []
    pcmds: list       = [
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
    pcmds.extend([
        ("SPAN",          (0, 0), (2, 0)),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
    ])
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
        pdata.append([Paragraph("  No payments received this period",
                                st["muted"]), "", ""])
        pcmds.append(("SPAN", (0, pri), (2, pri)))
        pri += 1

    pdata.append([Paragraph("Total Payments Received", st["bold"]),
                  "",
                  Paragraph(_fmt_amount(bill.summary.payments_received), st["rbold"])])
    pcmds.extend([
        ("LINEABOVE",     (0, pri), (-1, pri), 0.5, L.BOX_BORDER),
        ("TOPPADDING",    (0, pri), (-1, pri), 4),
    ])

    dw = _DESC_W - _DATE_W
    pmt_table = Table(pdata, colWidths=[dw, _DATE_W, _AMT_W], splitByRow=True)
    pmt_table.setStyle(TableStyle(pcmds))
    story.append(pmt_table)

    # ── I. Payment slip + legal (always last — anchored to bottom of last page)
    story.append(_SlipFlowable(bill))

    return story


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def render_bill(bill: Bill, out_path: str | None = None) -> str:
    """Render a Bill to PDF with automatic pagination. Returns path written."""
    if out_path is None:
        out_dir = Path("output")
        out_dir.mkdir(exist_ok=True)
        safe = bill.account_number.replace(" ", "-")
        out_path = str(out_dir / f"{safe}_{bill.period_start}_{bill.period_end}.pdf")

    # Measure where the content frame starts on page 1 (below A+B+C)
    frame_top = _measure_frame_top(bill)

    # Page-1 frame: from below section C all the way to the bottom margin.
    # The slip is now a flowable, so no space reservation is needed here.
    p1_frame = Frame(
        LEFT, MARGIN,
        CONTENT_W, max(frame_top - MARGIN, 1),
        leftPadding=0, rightPadding=0, topPadding=4, bottomPadding=0,
        showBoundary=0,
    )

    # Continuation-page frame: below the slim header to the bottom margin.
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
        # Legal notice and payment slip are rendered by _SlipFlowable in the story.

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
